from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Max
from django.template.defaulttags import comment
from django.utils import timezone


#alohida class yaratish hemis cuhun




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

    def __str__(self):
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
        related_name = 'teaching_courses'
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
    order = models.PositiveIntegerField(default=0)  # tartib uchun

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    def save(self, *args, **kwargs):
        if self.order is None:  # agar order bo‘sh bo‘lsa
            last_order = Section.objects.filter(course=self.course).aggregate(
                max_order=Max('order')
            )['max_order']
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']


class Missiya(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='missiya/', null=True, blank=True)




class Vazifa_bajarish(models.Model):
    file = models.FileField(upload_to='videos/')
    description = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    missiya = models.ForeignKey( Missiya, on_delete=models.CASCADE)
    user = models.ForeignKey( Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.text[10]} - {self.user.hemis_id}"


class SectionProgress(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)


# models.py ga qo'shimcha metodlar (Video modeliga)
class Video(models.Model):
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    small_description = models.TextField(null=True, blank=True)
    is_blocked = models.BooleanField(default=True)  # Dastlab barcha videolar bloklangan
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_next_video(self):
        """Keyingi videoni qaytarish order bo'yicha"""
        return Video.objects.filter(
            section=self.section,
            order__gt=self.order
        ).order_by('order').first()

    def check_video_access(self, user):
        """Video user uchun ochiq yoki yopiq ekanligini VideoProgress orqali tekshiradi"""

        # Admin va teacher uchun hamma ochiq
        if user.role in ['admin', 'teacher']:
            return True

        section_videos = Video.objects.filter(
            section=self.section
        ).order_by('order')

        if not section_videos.exists():
            return False

        # 1️⃣ Birinchi video doim ochiq
        first_video = section_videos.first()
        if self.id == first_video.id:
            return True

        # 2️⃣ Agar user shu videoni avval ko‘rgan bo‘lsa → ochiq
        if VideoProgress.objects.filter(
                user=user,
                video=self,
                is_completed=True
        ).exists():
            return True

        # 3️⃣ Oldingi video ko‘rilgan bo‘lsa → ochiq
        previous_video = section_videos.filter(
            order__lt=self.order
        ).order_by('-order').first()

        if not previous_video:
            return False

        return VideoProgress.objects.filter(
            user=user,
            video=previous_video,
            is_completed=True
        ).exists()

    def save(self, *args, **kwargs):
        # Birinchi video har doim ochiq bo‘lsin
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class VideoRating(models.Model):
    video = models.ForeignKey( Video, on_delete=models.CASCADE, related_name='ratings' )
    user = models.ForeignKey( Users, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField( validators=
                                               [ MinValueValidator(1),
                                                 MaxValueValidator(5)
                                               ]
                                               )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.video.title} - {self.rating} ⭐"



class Comment(models.Model):
    user = models.ForeignKey( Users, on_delete=models.CASCADE)
    video = models.ForeignKey( Video, on_delete=models.CASCADE, related_name='comments' )
    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.hemis_id} - {self.comment}"








# class Certificate(models.Model):
#     user = models.ForeignKey(Users, on_delete=models.CASCADE)
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     file = models.FileField(upload_to='certificates/')
#
#     def __str__(self):
#         return f"{self.course.title} - {self.user.hemis_id}"
#
#     class Meta:
#         ordering = ['created_at']
#         unique_together = ('course', 'user')




#videoni  tuliq kurishiga utkazish kerak yani 10 minutlik bvideopni kamida 8 minutini kurish kerak
