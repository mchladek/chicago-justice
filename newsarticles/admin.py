from django.contrib import admin
import newsarticles.models as models


@admin.register(models.Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('news_source', 'created', 'title',)


@admin.register(models.NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name',)


@admin.register(models.ScraperResult)
class ScraperResultAdmin(admin.ModelAdmin):
    list_display = ('news_source', 'completed_time', 'success',
                    'added_count', 'error_count', 'total_count')


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'abbreviation', 'kind', 'active')


@admin.register(models.UserCoding)
class UserCodingAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'date')
    search_fields = ['user__username']
    fields = ('article', 'date', 'user', 'relevant',
              'categories', 'locations', 'vict_age',
              'vict_race', 'vict_ethnicity', 'vict_sex', 'vict_name',
              'offend_age', 'offend_race', 'offend_ethnicity', 'offend_sex',
              'offend_name', 'offend_weap', 'sentiment')
    readonly_fields = ('article', 'date')


class TrainedCategoryRelevanceInline(admin.TabularInline):
    model = models.TrainedCategoryRelevance
    extra = 0
    can_delete = False
    readonly_fields = ('category', 'relevance',)

    def has_add_permission(self, request):
        False


class TrainedLocationInline(admin.TabularInline):
    model = models.TrainedLocation
    extra = 0
    can_delete = False
    readonly_fields = ('text', 'latitude', 'longitude',
                       'confidence', 'neighborhood')

    def has_add_permission(self, request):
        False


class TrainedSentimentInline(admin.TabularInline):
    model = models.TrainedSentiment
    fields = ('date', 'api_response')
    readonly_fields = ('date',)

    def has_add_permission(self, request):
        False


class TrainedSentimentEntitiesInline(admin.TabularInline):
    model = models.TrainedSentimentEntities
    extra = 0
    can_delete = False
    readonly_fields = ('response', 'index', 'entity', 'sentiment')

    def has_add_permission(self, request):
        False


@admin.register(models.TrainedCoding)
class TrainedCodingAdmin(admin.ModelAdmin):
    list_display = ('article', 'model_info', 'relevance', 'bin', 'sentiment_processed')
    inlines = [TrainedCategoryRelevanceInline, TrainedLocationInline, TrainedSentimentInline, TrainedSentimentEntitiesInline]
    readonly_fields = ('article', 'date', 'model_info', 'relevance',)
