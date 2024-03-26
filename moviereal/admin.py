from django.contrib import admin
from .models import Moviereal


# Register your models here.
# @admin.register(Moviereal)
# class xxx
# # 语法 admin.site.register(模型名)
# admin.site.register(Moviereal)


def sales_volume(g):
    total = g.price * g.sales
    return f'{g.name}销售额为:{total}'


sales_volume.short_description = '商品销售额'


# 方式一  利用装饰器注册方式
@admin.register(Moviereal)
class GoodsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock', 'sales', 'create_time', 'update_time', sales_volume)
    fields = ('name', 'price', 'stock')  # 用于控制编辑页要显示的字段，它的值是元组类型

    # fields选项支持以二维元组形式设置字段分栏显示，在fields中一个元组表示一栏数据
    # fields = (('name', 'price'), ('stock', 'sales'))

    # fieldsets选项用于对可编辑字段进行分组，该选项不可与ﬁelds选项同时使用
    # fieldsets = (
    #     ('商品基本信息', {'fields': ['name', 'stock', 'sales']}),
    #     ('商品价格信息', {'fields': ['price']})
    # )

    #  readonly fields选项中包含的字段会被设置为只读字段，该选项中包含的字段不可被编辑。
    # readonly_fields = ['sales']
    # save_on_top选项用于设置在编辑页上方是否显示保存、删除等按钮，默认为False,表示不显示
    # save_as = False

    # 设置字段链接,此处设置的字段可以作为连接点入
    list_display_links = ('id', 'name',)

    # 过滤器，可对此处设置的字段进行过滤
    # list_filter = ['sales', 'name']

    # 每页展示5条记录
    list_per_page = 5

    # 设置商品价格price为阅览列表可编辑字段
    # ps: list_display_links与list_editable不能同时设置同一字段
    list_editable = ('price',)

    # 表示以name,id 可以作为搜索字段
    search_fields = ('name', 'id')

    # 用于设置是否在顶部显示动作下拉框，默认为True，表示在顶部显示
    actions_on_top = False

    # 用于设置管理员动作是否在底部显示，默认为False，表示不在底部显示，当设置为True表示在底部显示。
    actions_on_bottom = False
