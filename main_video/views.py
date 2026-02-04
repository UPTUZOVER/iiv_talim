from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenObtainPairView

from django_filters.rest_framework import DjangoFilterBackend

import math

from main_video.models import *
from main_video.serializers import (
    MyTokenObtainPairSerializer,
    UserModelSerializer,
    CourseWithProgressSerializer,
    CategoryWithCoursesSerializer,
    SectionWithAccessSerializer,
    CategoryMainSerializer,
    SectionOneSerializer,
    SectionVazifaSerializer,
    VazifaSerializer,
    VideoProgressSerializer,
    CommentSerializer
)

from .serializers import VideosSerializer, VideoAccessSerializer, CourseMainSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserViewSet(ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UserModelSerializer
    parser_classes = (FormParser, MultiPartParser)




class UserOneViewSet(ModelViewSet):
    serializer_class = UserModelSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (FormParser, MultiPartParser)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Users.objects.none()
        return Users.objects.filter(hemis_id=self.request.user.hemis_id)



from rest_framework import viewsets, permissions

from .models import (
    Group, Users, Category, Course, CourseProgress, Section, Missiya,
    Vazifa_bajarish, SectionProgress, VideoRating, Comment
)
from .serializers import (
    GroupSerializer, CourseProgressSerializer, MissiyaSerializer, VazifaBajarishSerializer, SectionProgressSerializer,
    VideoRatingSerializer
)

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    # permission_classes = [permissions.IsAuthenticated]




class CourseProgressViewSet(viewsets.ModelViewSet):
    queryset = CourseProgress.objects.all()
    serializer_class = CourseProgressSerializer
    # permission_classes = [permissions.IsAuthenticated]


class MissiyaViewSet(viewsets.ModelViewSet):
    queryset = Missiya.objects.all()
    serializer_class = MissiyaSerializer
    # permission_classes = [permissions.IsAuthenticated]

class SectionProgressViewSet(viewsets.ModelViewSet):
    queryset = SectionProgress.objects.all()
    serializer_class = SectionProgressSerializer
    permission_classes = [permissions.IsAuthenticated]


from rest_framework import viewsets


class CategoryMainViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class =CategoryMainSerializer
import django_filters
from .models import Course


class CourseFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name='category_id')
    teacher = django_filters.NumberFilter(field_name='teacher__id')
    is_blocked = django_filters.BooleanFilter()

    class Meta:
        model = Course
        fields = ['category', 'teacher', 'is_blocked']



class CourseMainViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseMainSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_class = CourseFilter

    search_fields = [
        'title',
        'small_description',
        'author',
        'teacher__username',
    ]

    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryWithCoursesSerializer

    def get_serializer_context(self):
        """Request contextini serializer'ga o'tkazish"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideosSerializer
    permission_classes = [permissions.IsAuthenticated]  # Faqat avtorizatsiyalangan userlar

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['post'])
    def mark_as_watched(self, request, pk=None):
        """User videoni ko'rib bo'ldi deb belgilaydi"""
        video = self.get_object()
        user = request.user

        # Video'ga kirish huquqini tekshirish
        if not video.check_video_access(user):
            return Response({
                'error': 'Bu videoni ko‘rish huquqingiz yo‘q. Avval oldingi videoni ko‘rib bo‘lishingiz kerak.'
            }, status=status.HTTP_403_FORBIDDEN)

        # VideoProgressni yangilash yoki yaratish
        progress, created = VideoProgress.objects.get_or_create(
            user=user,
            video=video,
            defaults={'is_completed': True, 'completed_at': timezone.now()}
        )

        if not created:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()

        next_video = video.get_next_video()

        self._update_section_progress(user, video.section)

        self._update_course_progress(user, video.section.course)

        return Response({
            'success': True,
            'message': 'Video ko‘rib bo‘ldi',
            'video_id': video.id,
            'next_video_id': next_video.id if next_video and next_video.check_video_access(user) else None,
            'next_video_title': next_video.title if next_video and next_video.check_video_access(user) else None
        })

    @action(detail=True, methods=['get'])
    def check_access(self, request, pk=None):
        video = self.get_object()
        user = request.user

        has_access = video.check_video_access(user)
        next_video = video.get_next_video() if has_access else None

        serializer = VideoAccessSerializer({
            'has_access': has_access,
            'message': 'Mavjud' if has_access else 'Bloklangan',
            'next_video_id': next_video.id if next_video and next_video.check_video_access(user) else None
        })

        return Response(serializer.data)

    def _update_section_progress(self, user, section):

        videos = Video.objects.filter(section=section)
        total_videos = videos.count()

        completed_videos = VideoProgress.objects.filter(
            user=user,
            video__in=videos,
            is_completed=True
        ).count()

        progress_percent = math.floor((completed_videos / total_videos) * 100) if total_videos > 0 else 0
        is_completed = progress_percent == 100

        section_progress, _ = SectionProgress.objects.get_or_create(
            user=user,
            section=section
        )

        section_progress.is_completed = is_completed
        if is_completed and not section_progress.completed_at:
            section_progress.completed_at = timezone.now()
        section_progress.save()

    def _update_course_progress(self, user, course):
        sections = Section.objects.filter(course=course)
        total_sections = sections.count()

        completed_sections = SectionProgress.objects.filter(
            user=user,
            section__in=sections,
            is_completed=True
        ).count()

        progress_percent = math.floor((completed_sections / total_sections) * 100) if total_sections > 0 else 0
        is_completed = progress_percent == 100

        course_progress, _ = CourseProgress.objects.get_or_create(
            user=user,
            course=course
        )

        course_progress.progress_percent = progress_percent
        course_progress.is_completed = is_completed
        if is_completed and not course_progress.completed_at:
            course_progress.completed_at = timezone.now()
        course_progress.save()

from rest_framework.decorators import action
from rest_framework.response import Response

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionWithAccessSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def videos_with_access(self, request, pk=None):
        section = self.get_object()
        videos = Video.objects.filter(section=section).order_by('order')  # order bo'yicha

        result = []
        for video in videos:
            has_access = video.check_video_access(request.user)
            progress = VideoProgress.objects.filter(user=request.user, video=video).first()
            user_progress = {
                'is_completed': progress.is_completed if progress else False,
                'completed_at': progress.completed_at if progress else None
            }

            result.append({
                'id': video.id,
                'title': video.title,
                'order': video.order,
                'has_access': has_access,
                'user_progress': user_progress,
                'is_blocked': video.is_blocked,
                'small_description': video.small_description
            })

        return Response(result)



class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseWithProgressSerializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['get'])
    def user_progress(self, request, pk=None):
        course = self.get_object()
        user = request.user

        try:
            progress = CourseProgress.objects.get(
                user=user,
                course=course
            )
            serializer = CourseProgressSerializer(progress)
            return Response(serializer.data)
        except CourseProgress.DoesNotExist:
            return Response({
                'progress_percent': 0,
                'is_completed': False,
                'completed_at': None
            })

# main_video/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated

from main_video.models import Section, Quiz, Video, VideoProgress, QuizResult, SectionProgress
from main_video.serializers import SectionOneSerializer, QuizSubmitSerializer, QuizSerializer


class SectionOneViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.select_related('course', 'course__category')
    serializer_class = SectionOneSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'course': ['exact'],
        'course__category': ['exact'],
    }
    search_fields = ['title', 'small_description', 'course__title', 'course__category__title']
    ordering_fields = ['order', 'created_at']
    ordering = ['order']

    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def quiz(self, request, pk=None):
        """Sectiondagi quizni olish va is_accessible tekshirish"""
        section = self.get_object()
        quiz = section.quiz_set.first()  # sectiondagi quiz
        if not quiz:
            return Response({"detail": "Quiz mavjud emas"}, status=status.HTTP_404_NOT_FOUND)

        serializer = QuizSerializer(quiz, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit_quiz(self, request, pk=None):
        """Quiz javoblarini qabul qilish, ball hisoblash va natijani saqlash"""
        section = self.get_object()
        quiz = section.quiz_set.first()
        if not quiz:
            return Response({"detail": "Quiz mavjud emas"}, status=status.HTTP_404_NOT_FOUND)

        # Video progresslarni tekshirish
        videos = section.video_set.all()
        for video in videos:
            if not VideoProgress.objects.filter(user=request.user, video=video, is_completed=True).exists():
                return Response({"detail": "Barcha videolarni ko‘rib bo‘lmaganingiz sababli testga kirish mumkin emas"},
                                status=status.HTTP_403_FORBIDDEN)

        # QuizSubmitSerializer bilan javoblarni tekshirish
        serializer = QuizSubmitSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save(quiz)

        # Agar quiz pass bo‘lsa (60% yoki quiz.pass_percent)
        if result.percent >= quiz.pass_percent:
            # SectionProgress update
            section_progress, _ = SectionProgress.objects.get_or_create(user=request.user, section=section)
            section_progress.is_completed = True
            section_progress.completed_at = timezone.now()
            section_progress.save()

            # Keyingi section ochish
            next_section = Section.objects.filter(course=section.course, order__gt=section.order).order_by('order').first()
            if next_section:
                next_section.is_blocked = False
                next_section.save()

                # Keyingi sectiondagi birinchi video ham ochilsin
                first_video = next_section.video_set.order_by('order').first()
                if first_video:
                    first_video.is_accessible = True
                    first_video.save()

        return Response({
            "total_questions": result.total_questions,
            "correct_answers": result.correct_answers,
            "percent": result.percent,
            "is_passed": result.is_passed,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
        }, status=status.HTTP_200_OK)

from django.utils import timezone


def can_start_vazifalar(user, section):
    """Section vazifalarini ishlash uchun shart:
    - Sectiondagi -1 indexdagi video ko‘rilgan bo‘lishi kerak
    """
    last_video = Video.objects.filter(section=section).order_by('order').first()
    if not last_video:
        return False
    # user ushbu videoni ko‘rgan bo‘lishi kerak
    return VideoProgress.objects.filter(user=user, video=last_video, is_completed=True).exists()


def update_section_progress(user, section):
    """Sectiondagi vazifalar progressini hisoblash"""
    vazifalar = Vazifa_bajarish.objects.filter(missiya__section=section)
    total_vazifalar = vazifalar.values('missiya').distinct().count()

    if total_vazifalar == 0:
        return

    approved_scores = vazifalar.filter(user=user, is_approved=True).count()
    percent = (approved_scores / total_vazifalar) * 100

    section_progress, _ = SectionProgress.objects.get_or_create(user=user, section=section)
    section_progress.score_percent = percent
    section_progress.is_completed = percent >= 80
    if section_progress.is_completed and not section_progress.completed_at:
        section_progress.completed_at = timezone.now()
    section_progress.save()

    # keyingi sectionni ochish
    if section_progress.is_completed:
        next_section = Section.objects.filter(course=section.course, order__gt=section.order).order_by('order').first()
        if next_section:
            next_section.is_blocked = False
            next_section.save()





class SectionVazifasViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionVazifaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def vazifalar(self, request, pk=None):
        """Sectiondagi vazifalarni olish"""
        section = self.get_object()

        if not can_start_vazifalar(request.user, section):
            return Response({"error": "Vazifalarni ishlash uchun avval videoni ko‘rishingiz kerak."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(section)
        return Response(serializer.data)


class VazifaBajarishViewSet(viewsets.ModelViewSet):
    queryset = Vazifa_bajarish.objects.all()
    serializer_class = VazifaBajarishSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """User vazifa javobini yuboradi"""
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # section progressni yangilash
        section = serializer.instance.missiya.section
        update_section_progress(request.user, section)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Admin vazifani tasdiqlaydi"""
        vazifa = self.get_object()
        if request.user.role != 'admin':
            return Response({"error": "Faqat admin tasdiqlashi mumkin"}, status=status.HTTP_403_FORBIDDEN)

        score = request.data.get('score', 0)
        is_approved = request.data.get('is_approved', True)

        vazifa.score = score
        vazifa.is_approved = is_approved
        vazifa.save()

        # section progressni yangilash
        section = vazifa.missiya.section
        update_section_progress(vazifa.user, section)

        return Response({"success": True, "score": vazifa.score, "is_approved": vazifa.is_approved})



class AdminVazifaApproveViewSet(viewsets.ModelViewSet):
    queryset = Vazifa_bajarish.objects.all()
    serializer_class = VazifaSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        submission = self.get_object()
        score = request.data.get('score', 0)
        is_approved = request.data.get('is_approved', True)

        submission.is_approved = is_approved
        submission.score = score
        submission.save()

        # Section progressni tekshirish
        section = submission.missiya.section
        total = section.missiya_set.count() * 1  # har bir missiya uchun 1 ball (yoki foiz)
        approved = Vazifa_bajarish.objects.filter(
            missiya__section=section,
            user=submission.user,
            is_approved=True
        ).count()

        percent = (approved / total) * 100
        if percent >= 80:
            section.unlock_next_section()

        return Response({'success': True, 'percent_completed': percent})

class VideoProgresViews(viewsets.ModelViewSet):
    queryset = VideoProgress.objects.all()
    serializer_class = VideoProgressSerializer
    permission_classes = [IsAuthenticated]
# videolarni kurilgan qilib order bilan qilish kerak



class CommentPagination(PageNumberPagination):
    page_size = 10 # har bir sahifada 5 comment
    page_size_query_param = 'page_size'  # foydalanuvchi ?page_size=10 bilan o'zgartirishi mumkin
    max_page_size = 50


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CommentPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['video']



class RatingPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50



class VideoRatingViewSet(viewsets.ModelViewSet):
    queryset = VideoRating.objects.all()
    serializer_class = VideoRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = RatingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['video']




# main_video/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from main_video.models import Quiz, Question, QuizResult, VideoProgress, Section, SectionProgress
from main_video.serializers import QuizSubmitSerializer, QuizSerializer


class QuizViewSet(viewsets.ViewSet):
    """Quizga javob yuborish va natijalarni ko‘rish uchun API"""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Userning barcha quiz natijalarini ko‘rsatish"""
        user = request.user
        results = QuizResult.objects.filter(user=user).select_related('quiz', 'quiz__section')
        data = []
        for r in results:
            data.append({
                "quiz_id": r.quiz.id,
                "section_id": r.quiz.section.id,
                "section_title": r.quiz.section.title,
                "total_questions": r.total_questions,
                "correct_answers": r.correct_answers,
                "percent": r.percent,
                "is_passed": r.is_passed,
                "started_at": r.started_at,
                "finished_at": r.finished_at,
            })
        return Response(data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Frontenddan quiz javoblarini qabul qilish, ball hisoblash va natijani saqlash"""
        try:
            quiz = Quiz.objects.get(id=pk)
        except Quiz.DoesNotExist:
            return Response({"detail": "Quiz topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        # Video progresslarni tekshirish: barcha section videolari ko‘rilgan bo‘lishi kerak
        videos = quiz.section.video_set.all()
        for video in videos:
            if not VideoProgress.objects.filter(user=request.user, video=video, is_completed=True).exists():
                return Response({"detail": "Barcha videolarni ko‘rmaganingiz sababli testga kirish mumkin emas"},
                                status=status.HTTP_403_FORBIDDEN)

        # Javoblarni serializer orqali tekshirish
        serializer = QuizSubmitSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save(quiz)

        # Agar quiz pass bo‘lsa (60% yoki quiz.pass_percent)
        if result.percent >= quiz.pass_percent:
            # SectionProgress update
            section = quiz.section
            section_progress, _ = SectionProgress.objects.get_or_create(user=request.user, section=section)
            section_progress.is_completed = True
            section_progress.completed_at = timezone.now()
            section_progress.save()

            # Keyingi sectionni ochish
            next_section = Section.objects.filter(course=section.course, order__gt=section.order).order_by('order').first()
            if next_section:
                next_section.is_blocked = False
                next_section.save()

                # Keyingi sectiondagi birinchi video ham ochilsin
                first_video = next_section.video_set.order_by('order').first()
                if first_video:
                    first_video.is_accessible = True
                    first_video.save()

        return Response({
            "quiz_id": quiz.id,
            "section_id": quiz.section.id,
            "total_questions": result.total_questions,
            "correct_answers": result.correct_answers,
            "percent": result.percent,
            "is_passed": result.is_passed,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
        })



# main_video/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main_video.models import QuizResult

class QuizResultViewSet(viewsets.ViewSet):
    """
    User o‘ziga tegishli quiz natijalarini ko‘rishi uchun API
    Filter: ?section=<section_id>
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user

        # faqat shu userga tegishli natijalar
        queryset = QuizResult.objects.filter(
            user=user
        ).select_related(
            'quiz',
            'quiz__section',
            'quiz__section__course'
        )

        # 🔹 section bo‘yicha filter
        section_id = request.query_params.get('section')
        if section_id:
            queryset = queryset.filter(quiz__section_id=section_id)

        data = []
        for r in queryset:
            data.append({
                "quiz_id": r.quiz.id,
                "section_id": r.quiz.section.id,
                "section_title": r.quiz.section.title,
                "course_id": r.quiz.section.course.id,
                "course_title": r.quiz.section.course.title,

                "total_questions": r.total_questions,
                "correct_answers": r.correct_answers,
                "percent": r.percent,
                "is_passed": r.is_passed,

                "started_at": r.started_at,
                "finished_at": r.finished_at,
            })

        return Response(data, status=status.HTTP_200_OK)
