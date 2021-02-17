from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    slug = models.SlugField(max_length=160, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Subcategory(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    slug = models.SlugField(max_length=160, unique=True)
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"


class Product(models.Model):
    title = models.CharField(max_length=150, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    viewed = models.BooleanField(default=False)
    slug = models.SlugField(max_length=160, db_index=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    subcategory = models.ForeignKey(Subcategory, related_name='products', on_delete=models.PROTECT)

    def __str__(self):
        return self.title