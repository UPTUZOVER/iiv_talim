from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main_video.views import (
    MyTokenObtainPairView,
    UserViewSet,
    GroupViewSet,
    CategoryViewSet,
    CourseViewSet,
    CourseProgressViewSet,
    SectionViewSet,
    SectionProgressViewSet,
    MissiyaViewSet,
    VazifaBajarishViewSet,
    VideoViewSet,
    VideoRatingViewSet,
    CommentViewSet, CategoryMainViewSet, CourseMainViewSet, UserOneViewSet
)

router = DefaultRouter()

router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet, basename='groups')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'sections', SectionViewSet, basename='sections')
router.register(r'videos', VideoViewSet, basename='videos')
router.register(r'course-progress', CourseProgressViewSet, basename='course-progress')
router.register(r'section-progress', SectionProgressViewSet, basename='section-progress')
router.register(r'missiyas', MissiyaViewSet, basename='missiyas')
router.register(r'vazifas', VazifaBajarishViewSet, basename='vazifas')
router.register(r'video-ratings', VideoRatingViewSet, basename='video-ratings')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r"category_main", CategoryMainViewSet, basename='category-main')
router.register(r"course_main", CourseMainViewSet, basename='cource-main')
router.register(r"user_one",UserOneViewSet, basename='user-one')



urlpatterns = [
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/', include(router.urls)),
]












