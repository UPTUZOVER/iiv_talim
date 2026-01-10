from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from main_video.models import *
from main_video.serializers import MyTokenObtainPairSerializer, UserModelSerializer, \
    CourseWithProgressSerializer, CategoryWithCoursesSerializer, SectionWithAccessSerializer, CategoryMainSerializer, \
    CourseMainSerializer
from rest_framework.parsers import FormParser, MultiPartParser


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserViewSet(ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UserModelSerializer
    parser_classes = (FormParser, MultiPartParser)



from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser


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
    VideoRatingSerializer, CommentSerializer
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


class VazifaBajarishViewSet(viewsets.ModelViewSet):
    queryset = Vazifa_bajarish.objects.all()
    serializer_class = VazifaBajarishSerializer

class SectionProgressViewSet(viewsets.ModelViewSet):
    queryset = SectionProgress.objects.all()
    serializer_class = SectionProgressSerializer
    permission_classes = [permissions.IsAuthenticated]


from rest_framework import viewsets

class VideoRatingViewSet(viewsets.ModelViewSet):
    queryset = VideoRating.objects.all()
    serializer_class = VideoRatingSerializer
    permission_classes = [permissions.IsAuthenticated]


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

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

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course
from .serializers import CourseMainSerializer



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


from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import math

from .models import Video, VideoProgress, SectionProgress, CourseProgress, Section
from .serializers import VideosSerializer, VideoAccessSerializer

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

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionWithAccessSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['get'])
    def videos_with_access(self, request, pk=None):
        section = self.get_object()
        videos = Video.objects.filter(section=section).order_by('order')

        result = []
        for video in videos:
            has_access = video.check_video_access(request.user)
            user_progress = None

            try:
                progress = VideoProgress.objects.get(
                    user=request.user,
                    video=video
                )
                user_progress = {
                    'is_completed': progress.is_completed,
                    'completed_at': progress.completed_at
                }
            except VideoProgress.DoesNotExist:
                user_progress = {'is_completed': False, 'completed_at': None}

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


# videolarni kurilgan qilib order bilan qilish kerak