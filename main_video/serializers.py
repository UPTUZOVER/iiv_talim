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


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)

    class Meta:
        model = Users
        fields = ['id', 'hemis_id', 'first_name', 'last_name', 'role', 'group']








from rest_framework import serializers
from main_video.models import Video, Comment, VideoRating, Users

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # userni hemid ko‘rsatadi

    class Meta:
        model = Comment
        fields = ['id', 'user', 'video', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class VideoRatingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = VideoRating
        fields = ['id', 'user', 'video', 'rating', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating 1 dan 5 gacha bo‘lishi kerak")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        video = validated_data['video']

        # Agar user oldin rating bergan bo‘lsa, update qilamiz
        obj, created = VideoRating.objects.update_or_create(
            user=user,
            video=video,
            defaults={'rating': validated_data['rating']}
        )
        return obj




class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'video_file', 'small_description',
            'is_blocked', 'order', 'created_at', 'updated_at'
        ]

class VazifaBajarishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vazifa_bajarish
        fields = ['id', 'file', 'description', 'score', 'is_approved', 'missiya', 'user', 'created_at']

class Missiyas(serializers.ModelSerializer):
    vazifalar = VazifaBajarishSerializer(many=True, read_only=True)  # related_name='vazifalar'

    class Meta:
        model = Missiya
        fields = ['id', 'description', 'file', 'vazifalar']

class SectionVazifaSerializer(serializers.ModelSerializer):
    missiyas = Missiyas(many=True, read_only=True)  # related_name='missiyas'

    class Meta:
        model = Section
        fields = ['id', 'title', 'course', 'small_description', 'is_blocked', 'missiyas']



class MissiyaSerializer(serializers.ModelSerializer):
    vazifalar = VazifaBajarishSerializer(source='vazifa_bajarish_set', many=True, read_only=True)

    class Meta:
        model = Missiya
        fields = ['id', 'description', 'file', 'vazifalar']



class MissiyaOneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Missiya
        fields = ['id', 'description', 'file'   ]


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
    average_rating = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()   # 🆕 qo‘shildi

    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'video_file',
            'section',
            'small_description',
            'order',
            'is_accessible',
            'user_progress',
            'average_rating',
            'user_rating',     # 🆕 qo‘shildi
            'created_at',
            'updated_at'
        ]

    # 🔓 Video ochiq yoki yopiq
    def get_is_accessible(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.check_video_access(request.user)

    # 📊 User progress
    def get_user_progress(self, obj):
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

    # ⭐ O‘rtacha rating
    def get_average_rating(self, obj):
        avg = VideoRating.objects.filter(video=obj).aggregate(avg_rating=Avg('rating'))['avg_rating']
        return round(avg, 2) if avg else 0

    # 👤 USERNING O‘ZI BERGAN RATING
    def get_user_rating(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0

        rating = VideoRating.objects.filter(video=obj, user=request.user).first()
        return rating.rating if rating else 0


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

from django.db.models import Avg

class CourseWithProgressSerializer(serializers.ModelSerializer):
    """Kursni progress bilan birga, videolar o'rtacha rating bilan"""
    sections = serializers.SerializerMethodField()
    total_progress = serializers.SerializerMethodField()
    average_video_rating = serializers.SerializerMethodField()  # 🆕 yangi field
    teacher = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'teacher', 'category', 'img', 'author',
            'video', 'is_blocked', 'small_description', 'sections',
            'total_progress', 'average_video_rating',  # 🆕 qo‘shildi
            'created_at', 'updated_at'
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

    def get_average_video_rating(self, obj):
        """Kursdagi barcha videolarning o'rtacha ratingini hisoblash"""
        videos = Video.objects.filter(section__course=obj)
        avg = videos.aggregate(avg_rating=Avg('ratings__rating'))['avg_rating']  # ✅ 'videorating' → 'ratings'
        if avg is None:
            return 0
        return round(avg, 2)

class CategoryWithCoursesSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()  # 🆕 qo‘shildi

    class Meta:
        model = Category
        fields = [
            'id', 'title', 'img', 'courses', 'average_rating', 'created_at', 'updated_at'
        ]

    def get_courses(self, obj):
        request = self.context.get('request')
        courses = Course.objects.filter(category=obj)

        serializer = CourseWithProgressSerializer(
            courses,
            many=True,
            context={'request': request}
        )
        return serializer.data

    def get_average_rating(self, obj):
        videos = Video.objects.filter(section__course__category=obj)
        avg = videos.aggregate(avg_rating=Avg('ratings__rating'))['avg_rating']
        if avg is None:
            return 0
        return round(avg, 2)




class SectionOneSerializer(serializers.ModelSerializer):
    videos = VideosSerializer(source='video_set', many=True, read_only=True)
    missiyalar = MissiyaOneSerializer(source='missiyas', many=True, read_only=True)  # ✅ FIX

    category_id = serializers.IntegerField(
        source='course.category_id',
        read_only=True
    )

    class Meta:
        model = Section
        fields = [
            "id",
            "category_id",
            "title",
            "course",
            "order",
            "small_description",
            "is_blocked",
            "videos",
            "missiyalar"
        ]


class VazifaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vazifa_bajarish
        fields = ['id', 'missiya', "user",'description', 'file', 'is_approved', 'score']

