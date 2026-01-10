from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from main_video.models import (
    Users,
    Category,
    Course,
    CourseProgress,
    Section,
    SectionProgress,
    Video,
    VideoProgress,
    VideoRating,
    Missiya,
    Vazifa_bajarish,
    Comment,
    Group
)


# ----------------------------
# JWT Token Serializer
# ----------------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(  user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        return data


# ----------------------------
# User Serializer
# ----------------------------
class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'


from rest_framework import serializers
from .models import (
    Group, Users, Category, Course, CourseProgress, Section, Missiya,
    Vazifa_bajarish, SectionProgress, Video, VideoProgress, VideoRating, Comment
)


# -----------------------------
# GROUP SERIALIZER
# -----------------------------
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


# -----------------------------
# USER SERIALIZER
# -----------------------------
class UserSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)

    class Meta:
        model = Users
        fields = ['id', 'hemis_id', 'first_name', 'last_name', 'role', 'group']


# -----------------------------
# CATEGORY SERIALIZER
# -----------------------------


# -----------------------------
# VIDEO SERIALIZER
# -----------------------------
class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'video_file', 'small_description',
            'is_blocked', 'order', 'created_at', 'updated_at'
        ]


# -----------------------------
# COMMENT SERIALIZER
# -----------------------------
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'comment', 'created_at', 'updated_at']


# -----------------------------
# VIDEO RATING SERIALIZER
# -----------------------------
class VideoRatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = VideoRating
        fields = ['id', 'video', 'user', 'rating', 'created_at', 'updated_at']


# -----------------------------
# VAZIFA BAJARISH SERIALIZER
# -----------------------------
class VazifaBajarishSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vazifa_bajarish
        fields = ['id', 'file', 'description', 'user', 'missiya', 'created_at', 'updated_at']


# -----------------------------
# MISSIYA SERIALIZER
# -----------------------------
class MissiyaSerializer(serializers.ModelSerializer):
    vazifalar = VazifaBajarishSerializer(source='vazifa_bajarish_set', many=True, read_only=True)

    class Meta:
        model = Missiya
        fields = ['id', 'description', 'file', 'vazifalar']


# -----------------------------
# SECTION SERIALIZER
# -----------------------------
class SectionSerializer(serializers.ModelSerializer):
    videos = VideoSerializer(source='video_set', many=True, read_only=True)
    missiyalar = MissiyaSerializer(source='missiya_set', many=True, read_only=True)

    class Meta:
        model = Section
        fields = [
            'id', 'title', 'small_description', 'is_blocked', 'order',
            'created_at', 'updated_at', 'videos', 'missiyalar'
        ]



# -----------------------------
# COURSE SERIALIZER
# -----------------------------
class CourseSerializer(serializers.ModelSerializer):
    # teacher ManyToMany -> nested serializer, many=True
    teacher = UserSerializer(many=True, read_only=True)
    sections = SectionSerializer(source='section_set', many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'teacher', 'category', 'img', 'author',
            'video', 'is_blocked', 'small_description', 'created_at',
            'updated_at', 'sections'
        ]


class CategorySerializer(serializers.ModelSerializer):
    courses = CourseSerializer(source='course_set', many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'title', 'img',"courses", 'created_at', 'updated_at']



class CategoryMainSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'title', 'img', 'created_at', 'updated_at']


class CourseMainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"
# -----------------------------
# COURSE PROGRESS SERIALIZER
# -----------------------------
class CourseProgressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)


    class Meta:
        model = CourseProgress
        fields = ['id', 'user', 'course', 'progress_percent', 'is_completed', 'completed_at']


# -----------------------------
# SECTION PROGRESS SERIALIZER
# -----------------------------
class SectionProgressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    section = SectionSerializer(read_only=True)

    class Meta:
        model = SectionProgress
        fields = ['id', 'user', 'section', 'is_completed', 'completed_at']


# -----------------------------
# VIDEO PROGRESS SERIALIZER
# -----------------------------
class VideoProgressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    video = VideoSerializer(source='Section',
                            read_only=True)  # sizning modelda maydon nomi Section, shuning uchun source='Section'

    class Meta:
        model = VideoProgress
        fields = ['id', 'user', 'video', 'is_completed', 'completed_at']


# serializers.py ga qo'shimcha

from django.utils import timezone


class VideoAccessSerializer(serializers.Serializer):
    """Video'ga kirish huquqini tekshirish uchun"""
    has_access = serializers.BooleanField()
    message = serializers.CharField()
    next_video_id = serializers.IntegerField(required=False)



class VideosSerializer(serializers.ModelSerializer):
    is_accessible = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'video_file',
            'section',
            'small_description',
            'order',
            'is_accessible',      # 🔑 FRONTEND SHUNI TEKSHIRADI
            'user_progress',      # progress info
            'created_at',
            'updated_at'
        ]

    def get_is_accessible(self, obj):
        """
        Video user uchun ochiqmi yoki yo‘qmi
        FAqat VideoProgress + check_video_access orqali
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        return obj.check_video_access(request.user)

    def get_user_progress(self, obj):
        """
        Userning shu videodagi holati
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return {
                'is_completed': False,
                'completed_at': None
            }

        progress = VideoProgress.objects.filter(
            user=request.user,
            video=obj
        ).first()

        if not progress:
            return {
                'is_completed': False,
                'completed_at': None
            }

        return {
            'is_completed': progress.is_completed,
            'completed_at': progress.completed_at
        }

class SectionWithAccessSerializer(serializers.ModelSerializer):
    """User uchun bo'limdagi videolarni access bilan"""
    videos = VideosSerializer(many=True, read_only=True)
    accessible_videos_count = serializers.SerializerMethodField()
    total_videos_count = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            'id', 'title', 'course', 'small_description', 'is_blocked',
            'order', 'videos', 'accessible_videos_count', 'total_videos_count',
            'created_at', 'updated_at'
        ]

    def get_videos(self, obj):
        request = self.context.get('request')
        videos = Video.objects.filter(section=obj).order_by('order')

        if request and request.user.is_authenticated:
            serializer = VideosSerializer(
                videos,
                many=True,
                context={'request': request}
            )
            return serializer.data
        return []


    def get_accessible_videos_count(self, obj):
        """User uchun ochiq videolar soni"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            count = 0
            videos = Video.objects.filter(section=obj)
            for video in videos:
                if video.check_video_access(request.user):
                    count += 1
            return count
        return 0

    def get_total_videos_count(self, obj):
        """Jami videolar soni"""
        return Video.objects.filter(section=obj).count()


class CourseWithProgressSerializer(serializers.ModelSerializer):
    """Kursni progress bilan birga"""
    sections = serializers.SerializerMethodField()
    total_progress = serializers.SerializerMethodField()
    teacher = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'teacher', 'category', 'img', 'author',
            'video', 'is_blocked', 'small_description', 'sections',
            'total_progress', 'created_at', 'updated_at'
        ]

    def get_sections(self, obj):
        """Kursning bo'limlari"""
        request = self.context.get('request')
        sections = Section.objects.filter(course=obj).order_by('order')

        if request and request.user.is_authenticated:
            serializer = SectionWithAccessSerializer(
                sections,
                many=True,
                context={'request': request}
            )
            return serializer.data
        return []

    def get_total_progress(self, obj):
        """Kurs bo'yicha umumiy progress"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = CourseProgress.objects.get(
                    user=request.user,
                    course=obj
                )
                return progress.progress_percent
            except CourseProgress.DoesNotExist:
                return 0
        return 0


class CategoryWithCoursesSerializer(serializers.ModelSerializer):
    """Kategoriya va kurslari"""
    courses = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'title', 'img', 'courses', 'created_at', 'updated_at'
        ]

    def get_courses(self, obj):
        request = self.context.get('request')
        courses = Course.objects.filter(category=obj)

        # Kurslarni barcha foydalanuvchilar uchun chiqaramiz
        serializer = CourseWithProgressSerializer(
            courses,
            many=True,
            context={'request': request}  # request null bo'lsa ham ok, progress=0 bo'ladi
        )
        return serializer.data