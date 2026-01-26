from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Max
from django.utils import timezone


# ----------------------------
# User & Group
# ----------------------------
class Group(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Users(AbstractUser):
    hemis_id = models.CharField(max_length=255, unique=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    USERNAME_FIELD = 'hemis_id'
    REQUIRED_FIELDS = ['username']  # login qilish uchun boshqa required field

    def  __str__(self):
        return f"{self.hemis_id} ({self.role})"



class Category(models.Model):
    title = models.CharField(max_length=255)
    img = models.ImageField(upload_to="category/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('created_at',)
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.title


class Course(models.Model):
    title = models.CharField(max_length=255)
    teacher = models.ManyToManyField(
        Users,
        limit_choices_to={'role': 'teacher'},  # faqat teacherlar chiqadi
        blank=True,
        related_name='teaching_courses'
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    img = models.ImageField(upload_to='courses/', null=True, blank=True)
    author = models.CharField(max_length=255)
    video = models.FileField(upload_to='courses/', null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    small_description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CourseProgress(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)



class Section(models.Model):
    title = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    small_description = models.TextField()
    is_blocked = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.order:  # agar order bo‘sh bo‘lsa
            last_order = Section.objects.filter(course=self.course).aggregate(max_order=Max('order'))['max_order']
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class SectionProgress(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    score_percent = models.FloatField(default=0)



class Missiya(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='missiyas')
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='missiya/', null=True, blank=True)


class Vazifa_bajarish(models.Model):
    missiya = models.ForeignKey(Missiya, on_delete=models.CASCADE, related_name='vazifalar')
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    file = models.FileField(upload_to='vazifalar/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    score = models.PositiveSmallIntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class Video(models.Model):
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    small_description = models.TextField(null=True, blank=True)
    is_blocked = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

    def get_next_video(self):
        return Video.objects.filter(section=self.section, order__gt=self.order).order_by('order').first()

    def check_video_access(self, user):
        # Admin va teacher uchun hamma ochiq
        if user.role in ['admin', 'teacher']:
            return True

        section_videos = Video.objects.filter(section=self.section).order_by('order')
        if not section_videos.exists():
            return False

        first_video = section_videos.first()
        if self.id == first_video.id:
            return True

        if VideoProgress.objects.filter(user=user, video=self, is_completed=True).exists():
            return True

        previous_video = section_videos.filter(order__lt=self.order).order_by('-order').first()
        if previous_video:
            return VideoProgress.objects.filter(user=user, video=previous_video, is_completed=True).exists()
        return False

    def save(self, *args, **kwargs):
        section_videos = Video.objects.filter(section=self.section).order_by('order')
        first_video = section_videos.first()
        if first_video and self.id == first_video.id:
            self.is_blocked = False
        super().save(*args, **kwargs)


class VideoProgress(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'video')

    def __str__(self):
        return f"{self.user.hemis_id} - {self.video.title} - {self.is_completed}"


class VideoRating(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.video.title} - {self.rating} ⭐"





class Comment(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.hemis_id} - {self.comment}"
