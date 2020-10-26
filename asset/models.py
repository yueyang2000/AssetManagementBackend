'''asset model'''

from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from users.models import User
from department.models import Department


class Asset(models.Model):
    ''' asset model '''
    name = models.CharField(max_length=30, null=False, verbose_name='资产名称')
    quantity = models.IntegerField(verbose_name='数量', default=1)
    value = models.IntegerField(verbose_name='资产价值', default=1)

    # 这种记录方式很不利于开发，需要改成choices
    is_quantity = models.BooleanField(verbose_name='资产类型', default=False)

    description = models.CharField(max_length=150, verbose_name='简介', blank=True, default='')
    parent = models.CharField(max_length=20, verbose_name='父资产', blank=True, default='')
    child = models.CharField(max_length=100, verbose_name='子资产', blank=True, default='')

    status_choices = [('IDLE', '闲置'),
                      ('IN_USE', '使用'),
                      ('IN_MAINTAIN', '维护'),
                      ('RETIRED', '清退'),
                      ('DELETED', '删除')]

    status = models.CharField(max_length=20, choices=status_choices, default='IDLE')
    start_time = models.DateTimeField(verbose_name='录入时间', auto_now_add=True)
    owner = models.ForeignKey(User, verbose_name='挂账人', on_delete=models.SET(User.admin))

    @property
    def department(self) -> Department:
        ''' 所属部门，即所属用户的部门 '''
        return self.owner.department

    @property
    def now_value(self) -> int:
        ''' 资产折旧后的价值 '''
        return self.value


class AssetCatagory(MPTTModel):
    '''Asset Catagory'''
    name = models.CharField(max_length=30, verbose_name='资产分类')
    parent = TreeForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)

    @classmethod
    def root(cls):
        ''' 返回顶层类型 '''
        return cls.objects.first().get_root()
