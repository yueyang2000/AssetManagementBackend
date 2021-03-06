'''views for app asset'''
from django.db.utils import IntegrityError
from mptt.exceptions import InvalidMove

from app.utils import (catch_exception, gen_response, parse_args, parse_list,
                       visit_tree)
from department.models import Department
from user.utils import auth_permission_required

from .models import Asset, AssetCategory, CustomAttr, AssetCustomAttr
from .utils import gen_history, get_assets_list


@catch_exception('GET')
@auth_permission_required()
def asset_list(request):
    '''api/asset/list GET
    return an asset list for asset manager'''
    department = request.user.department
    all_assets = Asset.objects.filter(owner__department=department)
    res = get_assets_list(all_assets)
    return gen_response(code=200, data=res)


@catch_exception('POST')
@auth_permission_required()
def asset_add(request):
    '''  api/asset/add POST
    资产管理员添加资产，需要提供的条目：
    value, name, category, description, parent_id, custom
    return: code =
        200: success
        201: parameter error
        400: Validation Error when saving asset
    '''
    pack_list = parse_list(
        request.body,
        'value',
        'name', 'category', 'description',
        'service_life', 'parent_id', 'custom',
        description='', service_life=5,
        parent_id=-1, custom={}
    )

    for pack in pack_list:
        value, name, category, description, service_life, parent_id, custom = pack
        category = AssetCategory.objects.get(name=category)

        try:
            parent: Asset = Asset.objects.get(id=parent_id)
        except Asset.DoesNotExist:
            parent = None
        else:
            if parent.status != 'IDLE':
                return gen_response(code=204, message='只能指定空闲资产为父资产')
        asset = Asset(
            value=value,
            name=name,
            category=category,
            description=description,
            owner=request.user,
            status='IDLE',
            service_life=service_life,
            parent=parent
        )
        asset.full_clean()
        asset.save()
        AssetCustomAttr.update_custom_attrs(asset, custom)
    return gen_response(code=200, message=f'添加资产 {len(pack_list)} 条')


@catch_exception('POST')
@auth_permission_required()
def asset_edit(request):
    '''  api/asset/edit POST
    编辑资产
    可编辑的条目有：name, description, parent_id
    return: code =
        200: success
        201: parameter error
        202：no such asset
    '''
    nid, name, description, parent_id, custom = parse_args(
        request.body,
        'nid', 'name', 'description', 'parent_id', 'custom',
        parent_id='', custom={})

    asset = Asset.objects.get(id=nid)
    try:
        parent = Asset.objects.get(id=parent_id)
    except ValueError:
        parent = None
    else:
        if parent.status != 'IDLE' or asset.status != 'IDLE':
            return gen_response(code=204, message='只能修改空闲资产间的父子关系')

    asset.name, asset.parent = name, parent
    asset.description = description
    try:
        asset.save()
        AssetCustomAttr.update_custom_attrs(asset, custom)
    except InvalidMove:
        return gen_response(code=203, message='无法指定自己成为自己的父资产')
    return gen_response(code=200, message=f'修改资产 {asset.name} 信息')


@catch_exception('POST')
@auth_permission_required()
def asset_history(request):
    ''' api/asset/history POST
    para: nid(int)
    return: code = ...
    data = [
        {time(str), user(str), type(str), info(str)}, ...
    ]
    '''
    nid = parse_args(request.body, 'nid')[0]
    asset = Asset.objects.get(id=nid)
    history = asset.history.all()
    res = [gen_history(record) for record in history]
    return gen_response(code=200, data=res)


@catch_exception('GET')
@auth_permission_required()
def asset_available_list(request):
    '''api/asset/available GET
    返回可以领用(IDLE)的资产
    '''
    department = request.user.department
    all_assets = Asset.objects.filter(owner__department=department, status='IDLE')
    res = get_assets_list(all_assets)
    return gen_response(code=200, data=res)


@catch_exception('POST')
@auth_permission_required()
def asset_query(request):
    ''' api/asset/query POST
    para: name(str), category(str), description(str)
    '''
    args = parse_args(request.body,
                      'name', 'category', 'description',
                      'customKey', 'customValue',
                      name='', category='', description='',
                      customKey='', customValue='')
    name, category, description, key, value = args
    assets = Asset.objects.filter(owner__department=request.user.department)
    assets = assets.filter(name__contains=name)
    assets = assets.filter(description__contains=description)
    if category != '':
        category = AssetCategory.objects.get(name=category)
        assets = assets.filter(category=category)
    if key != '':
        assets = AssetCustomAttr.search_custom_attr(key, value, assets)
    res = get_assets_list(assets)
    return gen_response(data=res, code=200)


@catch_exception('POST')
@auth_permission_required()
def asset_retire(request):
    ''' api/asset/retire POST
    para: nid(int) 资产id, retire_family(bool) 是否清退关联资产
    '''
    nid, retire_family = parse_args(request.body, 'nid', 'retire_family', retire_family=False)
    asset: Asset = Asset.objects.get(id=int(nid))
    if asset.status != 'IDLE':
        return gen_response(code=203, message='只能清退空闲中的资产')
    asset.status = 'RETIRED'
    asset._change_reason = '清退'
    if retire_family:
        asset.save(tree_update=True)
    else:
        asset.parent = None
        asset.save()
        Asset.objects.filter(parent=asset).update(parent=None)
    return gen_response(code=200, message=f'清退资产 {asset.name}')


@catch_exception('GET')
@auth_permission_required()
def category_tree(request):
    ''' api/asset/category/tree GET'''
    root = AssetCategory.root()
    res = visit_tree(root)
    return gen_response(code=200, data=res)


@catch_exception('POST')
@auth_permission_required()
def category_add(request):
    ''' api/asset/category/add POST
    para: parent_id(int), name(str)
    return: code =
        200: success
    '''
    parent_id, category_name = parse_args(request.body, 'parent_id', 'name')
    parent = AssetCategory.objects.get(id=parent_id)
    try:
        AssetCategory.objects.create(name=category_name, parent=parent)
    except IntegrityError:
        return gen_response(code=203, message="类型名不能重复")
    return gen_response(code=200, message=f'添加资产类别 {category_name}')


@catch_exception('POST')
@auth_permission_required()
def category_delete(request):
    ''' api/asset/category/delete POST
    para: id(int)
    return: code =
        200: success
        201: parameter error
        202: 对应部门不存在
        203: 顶层部门不能删除
    '''
    category_id = parse_args(request.body, 'id')[0]

    if int(category_id) == AssetCategory.root().id:
        return gen_response(code=203, message='顶级资产类型不能删除')

    category = AssetCategory.objects.get(id=category_id)
    category.delete()
    return gen_response(code=200, message=f'删除资产类别 {category.name}')


@catch_exception('POST')
@auth_permission_required()
def category_edit(request):
    ''' api/asset/category/edit POST
    para: id(int), name(str)
    return: code =
        200: success
    '''
    category_id, name = parse_args(request.body, 'id', 'name')
    category = AssetCategory.objects.get(id=category_id)

    old_name, category.name = category.name, name
    try:
        category.save()
    except IntegrityError:
        return gen_response(code=203, message="类型名不能重复")
    return gen_response(code=200, message=f'将资产类别 {old_name} 更名为 {name}')


@catch_exception('POST')
@auth_permission_required()
def custom_attr_edit(request):
    ''' api/asset/custom/edit POST
    修改自定义属性
    para:
        - custom(list)
    '''
    attrs = parse_args(request.body, 'custom')[0]
    CustomAttr.objects.all().delete()
    for attr in attrs:
        try:
            CustomAttr.objects.create(name=attr)
        except IntegrityError:
            return gen_response(code=203, message='不能设置两个相同自定义属性')
    return gen_response(code=200, message='修改自定义属性')


@catch_exception('GET')
@auth_permission_required()
def custom_attr_list(request):
    '''
    api/asset/custom/list GET
    获得自定义属性
    '''
    attrs = CustomAttr.objects.filter()
    res = [attr.name for attr in attrs]
    return gen_response(code=200, data=res)


@catch_exception('POST')
@auth_permission_required()
def asset_allocate(request):
    ''' /api/asset/allocate POST
    调拨资产到请求者(资产管理员)的部门中
    para:  '''
    asset_id_list, department_id = parse_args(request.body, 'idList', 'id')
    department: Department = Department.objects.get(id=department_id)
    target_manager = department.get_asset_manager()
    if target_manager is None:
        return gen_response(code=203, message=f'{department.name} 没有资产管理员')
    assets = set()
    for nid in asset_id_list:
        asset: Asset = Asset.objects.get(id=nid)
        assets.update(asset.get_entire_tree())
    for asset in assets:
        asset.owner = target_manager
        asset._change_reason = '调拨'
        asset.save()
    return gen_response(code=200,
                        message=f'{request.user.username} 向部门 {department.name} '
                                f'调拨 {len(asset_id_list)}资产')
