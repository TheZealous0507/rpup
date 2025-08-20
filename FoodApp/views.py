import time

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import pymysql
from django.conf import settings
import hashlib
import os
import html
from datetime import datetime

# 添加文件处理相关导入
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def get_database_connection():
    """
    获取数据库连接
    """
    db_config = settings.DATABASES['default']
    connection = pymysql.connect(
        host=db_config['HOST'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        database=db_config['NAME'],
        port=int(db_config['PORT']),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'  # 支持emoji存储
    )
    return connection

def index(request):
    """
    主页视图函数
    """
    # 从session中获取用户信息
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    # 优先使用session中的头像HTML
    avatar_html = request.session.get('avatar_html')
    
    # 如果session中没有头像HTML，则按原有逻辑处理
    if not avatar_html and user_id:
        avatar = request.session.get('avatar')
        # 后端处理头像显示逻辑，直接传递给前端显示
        if avatar:
            # 判断是否为上传的图片头像
            if avatar.isdigit():
                # 预设头像 (1-7)
                avatar_html = f'<img src="/media/avatars/{avatar}.png" alt="头像" class="user-avatar">'
            elif not avatar.startswith('&#x'):
                # 上传的图片头像
                avatar_html = f'<img src="/media/avatars/{avatar}" alt="头像" class="user-avatar">'
            else:
                # emoji头像 - 使用默认头像1.png
                avatar_html = '<img src="/media/avatars/1.png" alt="头像" class="user-avatar">'
        else:
            # 默认头像
            avatar_html = '<img src="/media/avatars/1.png" alt="头像" class="user-avatar>'
    
    context = {
        'user_id': user_id,
        'username': username,
        'avatar': avatar_html,
    }
    return render(request, 'FoodApp/index.html', context)

def register(request):
    """
    用户注册视图函数 - 第一步：账户基本信息
    """
    if request.method == 'POST':
        # 用户基本信息
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        # 处理头像选择
        avatar_type = request.POST.get('avatar_type', 'emoji')  # emoji 或 upload
        avatar = '1'  # 默认头像为1.png
        
        if avatar_type == 'emoji':
            # 对于预设头像，直接使用选择的数字值
            avatar = request.POST.get('avatar_emoji', '1')
        elif avatar_type == 'upload' and request.FILES.get('avatar_upload'):
            # 处理上传的头像文件
            avatar_file = request.FILES['avatar_upload']
            # 生成文件名
            file_extension = avatar_file.name.split('.')[-1]
            file_name = f"{username}_avatar.{file_extension}"
            # 保存文件
            path = default_storage.save(f'avatars/{file_name}', ContentFile(avatar_file.read()))
            avatar = path  # 保存文件路径

        # 检查密码是否匹配
        if password != confirm_password:
            messages.error(request, '两次输入的密码不一致')
            return render(request, 'FoodApp/register.html')
        
        # 检查用户名是否已存在
        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                messages.error(request, '用户名已存在')
                return render(request, 'FoodApp/register.html')
            
            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                messages.error(request, '邮箱已被注册')
                return render(request, 'FoodApp/register.html')
            
            cursor.close()
            connection.close()
            
            # 将基本信息存储在session中
            request.session['registration_data'] = {
                'username': username,
                'email': email,
                'password': password,
                'avatar': avatar if avatar else '1'  # 保存头像选择，默认为1.png
            }
            
            # 转到第二步：个人信息
            return redirect('FoodApp:register_personal')
            
        except Exception as e:
            messages.error(request, f'注册失败: {str(e)}')
            return render(request, 'FoodApp/register.html')
    
    return render(request, 'FoodApp/register.html')

def register_personal(request):
    """
    用户注册视图函数 - 第二步：个人信息
    """
    # 检查是否有第一步的数据
    if 'registration_data' not in request.session:
        return redirect('FoodApp:register')
    
    if request.method == 'POST':
        # 用户身体信息
        full_name = request.POST['full_name']
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        activity_level = request.POST.get('activity_level')
        
        # 将个人信息添加到session中
        registration_data = request.session['registration_data']
        registration_data.update({
            'full_name': full_name,
            'age': age,
            'gender': gender,
            'height': height,
            'weight': weight,
            'activity_level': activity_level
        })
        request.session['registration_data'] = registration_data
        
        # 转到第三步：健身目标
        return redirect('FoodApp:register_goals')
    
    return render(request, 'FoodApp/register_personal.html')

def register_goals(request):
    """
    用户注册视图函数 - 第三步：健身目标
    """
    # 检查是否有第一步和第二步的数据
    if 'registration_data' not in request.session:
        return redirect('FoodApp:register')
    
    if request.method == 'POST':
        # 目标信息
        goal_type = request.POST.get('goal_type')
        target_weight = request.POST.get('target_weight')
        target_date = request.POST.get('target_date')
        daily_calorie_goal = request.POST.get('daily_calorie_goal')
        
        # 将目标信息添加到session中
        registration_data = request.session['registration_data']
        registration_data.update({
            'goal_type': goal_type,
            'target_weight': target_weight,
            'target_date': target_date,
            'daily_calorie_goal': daily_calorie_goal
        })
        request.session['registration_data'] = registration_data
        
        # 执行最终注册
        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 插入新用户（使用hash算法加密密码）
            password_hash = hashlib.sha256(registration_data['password'].encode()).hexdigest()
            
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, full_name, age, gender, height, weight, activity_level, avatar) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (registration_data['username'], registration_data['email'], password_hash, 
                 registration_data['full_name'], registration_data['age'], registration_data['gender'],
                 registration_data['height'], registration_data['weight'], registration_data['activity_level'],
                 registration_data['avatar'])  # 添加avatar字段
            )
            
            user_id = cursor.lastrowid
            
            # 如果用户设置了目标，则插入目标信息
            if registration_data['goal_type'] and registration_data['daily_calorie_goal']:
                cursor.execute(
                    """INSERT INTO goals (user_id, goal_type, target_weight, target_date, daily_calorie_goal) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (user_id, registration_data['goal_type'], registration_data['target_weight'], 
                     registration_data['target_date'], registration_data['daily_calorie_goal'])
                )
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # 清除session中的注册数据
            if 'registration_data' in request.session:
                del request.session['registration_data']
            
            # 登录成功，设置session
            request.session['user_id'] = user_id
            request.session['username'] = registration_data['username']
            
            # 存储avatar，让后端处理类型判断
            avatar = registration_data['avatar'] if registration_data['avatar'] else '1'
            request.session['avatar'] = avatar
            
            # 处理头像显示逻辑，直接传递给前端显示
            if avatar.isdigit():
                # 预设头像 (1-7)
                avatar_html = f'<img src="/media/avatars/{avatar}.png" alt="头像" class="user-avatar">'
            elif not avatar.startswith('&#x'):
                # 上传的图片头像
                avatar_html = f'<img src="/media/avatars/{avatar}" alt="头像" class="user-avatar">'
            else:
                # emoji头像 - 使用默认头像1.png
                avatar_html = '<img src="/media/avatars/1.png" alt="头像" class="user-avatar">'
            
            # 将头像HTML存储在session中
            request.session['avatar_html'] = avatar_html
            
            # 重定向到主页
            return redirect('FoodApp:index')
            
        except Exception as e:
            messages.error(request, f'注册失败: {str(e)}')
            return render(request, 'FoodApp/register_goals.html')
    
    return render(request, 'FoodApp/register_goals.html')

def login(request):
    """
    用户登录视图函数
    """
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 查询用户信息
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("SELECT id, username, avatar FROM users WHERE username = %s AND password_hash = %s", 
                          (username, password_hash))
            user = cursor.fetchone()
            
            if user:
                # 登录成功，设置session
                request.session['user_id'] = user['id']
                request.session['username'] = user['username']
                # 存储avatar，让后端处理类型判断
                avatar = user['avatar'] if user['avatar'] else '1'
                request.session['avatar'] = avatar
                
                # 处理头像显示逻辑，直接传递给前端显示
                if avatar.isdigit():
                    # 预设头像 (1-7)
                    avatar_html = f'<img src="/media/avatars/{avatar}.png" alt="头像" class="user-avatar">'
                elif not avatar.startswith('&#x'):
                    # 上传的图片头像
                    avatar_html = f'<img src="/media/avatars/{avatar}" alt="头像" class="user-avatar">'
                else:
                    # emoji头像 - 使用默认头像1.png
                    avatar_html = '<img src="/media/avatars/1.png" alt="头像" class="user-avatar">'
                
                # 将头像HTML存储在session中
                request.session['avatar_html'] = avatar_html
                
                messages.success(request, '登录成功')
                return redirect('FoodApp:index')
            else:
                messages.error(request, '用户名或密码错误')
                
            cursor.close()
            connection.close()
            
        except Exception as e:
            messages.error(request, f'登录失败: {str(e)}')
    
    return render(request, 'FoodApp/login.html')

def logout(request):
    """
    用户退出登录视图函数
    """
    # 清除用户的session数据
    request.session.flush()
    return redirect('FoodApp:index')

def food_search(request):
    """
    食物搜索视图函数
    """
    context = {
        'user_id': request.session.get('user_id'),
        'username': request.session.get('username'),
        'avatar': request.session.get('avatar_html'),
    }
    
    query = request.GET.get('q', '').strip()
    
    # 处理添加食物到数据库的请求
    if request.method == 'POST' and 'add_to_database' in request.POST:
        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 获取表单数据
            food_name = request.POST.get('food_name')
            calories = request.POST.get('calories_per_100g')
            protein = request.POST.get('protein_per_100g')
            carbs = request.POST.get('carbs_per_100g')
            fat = request.POST.get('fat_per_100g')
            
            # 插入到数据库
            insert_sql = """
                INSERT INTO foods (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (food_name, calories, protein, carbs, fat))
            connection.commit()
            
            messages.success(request, f'食物"{food_name}"已成功添加到数据库中！')
            
            cursor.close()
            connection.close()
            
            # 重定向以避免重复提交
            return redirect(f"{request.path}?q={query}")
        except Exception as e:
            messages.error(request, f'添加食物失败: {str(e)}')
    
    if query:
        context['query'] = query
        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 首先在本地数据库中搜索
            sql = """
                SELECT id, name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g 
                FROM foods 
                WHERE name LIKE %s
                ORDER BY name
            """
            search_term = f"%{query}%"
            cursor.execute(sql, (search_term,))
            foods = cursor.fetchall()
            
            context['foods'] = foods
            
            # 如果本地数据库中没有找到，调用AI接口
            if not foods:
                try:
                    import json
                    import logging
                    import requests
                    from django.conf import settings
                    
                    # 设置日志记录
                    logger = logging.getLogger(__name__)
                    
                    # 准备请求头和载荷
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.XFYUN_API_KEY}"
                    }
                    
                    prompt = f"请告诉我{query}这种食物每100克的营养成分，包括热量（千卡）、蛋白质（克）、碳水化合物（克）和脂肪（克）。以JSON格式返回结果，格式如下：{{\"name\": \"{query}\", \"calories\": 数值, \"protein\": 数值, \"carbs\": 数值, \"fat\": 数值}}。只返回JSON，不要其他内容。"
                    
                    payload = {
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "model": "lite",  # 使用lite模型
                        "stream": False
                    }

                    # 发送请求
                    response = requests.post(
                        settings.XFYUN_API_URL, 
                        json=payload, 
                        headers=headers, 
                        timeout=120
                    )
                    response.raise_for_status()

                    content = response.json()['choices'][0]['message']['content'].strip()
                    logger.info(f"API返回原始内容: {content}")
                    
                    # 处理可能的代码块格式
                    if content.startswith("```json"):
                        content = content[7:]  # 移除 ```json
                    if content.endswith('```'):
                        content = content[:-3]  # 移除 ```
                    
                    # 解析JSON
                    try:
                        api_result = json.loads(content)
                        context['api_result'] = api_result
                    except json.JSONDecodeError:
                        # 如果解析失败，记录原始内容
                        logger.error(f"JSON解析失败，原始内容: {content}")
                        context['api_result'] = None
                    
                except Exception as e:
                    # 出错时记录日志
                    logger.error(f"AI服务调用出现错误: {str(e)}")
                    context['api_result'] = None
                    
            cursor.close()
            connection.close()
            
        except Exception as e:
            messages.error(request, f'搜索失败: {str(e)}')
    
    return render(request, 'FoodApp/food_search.html', context)

def food_search_ajax(request):
    """
    AJAX搜索食物视图函数
    """
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET['q'].strip()
        if query:
            try:
                connection = get_database_connection()
                cursor = connection.cursor()
                
                # 执行模糊查询
                sql = """
                    SELECT id, name, calories_per_100g as calories, protein_per_100g as protein, 
                           carbs_per_100g as carbs, fat_per_100g as fat 
                    FROM foods 
                    WHERE name LIKE %s
                    ORDER BY name
                """
                search_term = f"%{query}%"
                cursor.execute(sql, (search_term,))
                foods = cursor.fetchall()
                
                cursor.close()
                connection.close()
                
                return JsonResponse({'foods': foods})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'foods': []})


def food_search_api(request):
    """
    调用API搜索食物视图函数
    """
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET['q'].strip()
        if query:
            try:
                import json
                import logging
                import requests
                from django.conf import settings
                
                # 设置日志记录
                logger = logging.getLogger(__name__)
                
                # 准备请求头和载荷
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.XFYUN_API_KEY}"
                }
                
                prompt = f"请告诉我{query}这种食物每100克的营养成分，包括热量（千卡）、蛋白质（克）、碳水化合物（克）和脂肪（克）。以JSON格式返回结果，格式如下：{{\"name\": \"{query}\", \"calories\": 数值, \"protein\": 数值, \"carbs\": 数值, \"fat\": 数值}}。只返回JSON，不要其他内容。"
                
                payload = {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "model": "lite",  # 使用lite模型
                    "stream": False
                }

                # 发送请求
                response = requests.post(
                    settings.XFYUN_API_URL, 
                    json=payload, 
                    headers=headers, 
                    timeout=120
                )
                response.raise_for_status()

                content = response.json()['choices'][0]['message']['content'].strip()
                logger.info(f"API返回原始内容: {content}")
                
                # 处理可能的代码块格式
                if content.startswith("```json"):
                    content = content[7:]  # 移除 ```json
                if content.endswith('```'):
                    content = content[:-3]  # 移除 ```
                
                # 解析JSON
                try:
                    api_result = json.loads(content)
                    return JsonResponse({'foods': api_result})
                except json.JSONDecodeError:
                    # 如果解析失败，记录原始内容
                    logger.error(f"JSON解析失败，原始内容: {content}")
                    return JsonResponse({'error': 'JSON解析失败'}, status=500)
            except Exception as e:
                # 出错时记录日志
                logger.error(f"AI服务调用出现错误: {str(e)}")
                return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '无效的请求'}, status=400)

def meal_search_food(request):
    """
    添加餐食页面搜索食物视图函数
    """
    print(666666666666666666666)
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET['q'].strip()
        if query:
            try:
                connection = get_database_connection()
                cursor = connection.cursor()
                
                # 执行模糊查询
                sql = """
                    SELECT id, name, calories_per_100g as calories, protein_per_100g as protein, 
                           carbs_per_100g as carbs, fat_per_100g as fat 
                    FROM foods 
                    WHERE name LIKE %s
                    ORDER BY name
                """
                search_term = f"%{query}%"
                cursor.execute(sql, (search_term,))
                foods = cursor.fetchall()
                
                cursor.close()
                connection.close()

                # 确保返回的数据格式正确
                foods_list = []
                for food in foods:
                    foods_list.append({
                        'id': food['id'],
                        'name': food['name'],
                        'calories': float(food['calories']) if food['calories'] else 0,
                        'protein': float(food['protein']) if food['protein'] else 0,
                        'carbs': float(food['carbs']) if food['carbs'] else 0,
                        'fat': float(food['fat']) if food['fat'] else 0
                    })
                    print(food)
                return JsonResponse({'foods': foods_list})
            except Exception as e:
                # 如果是AJAX请求，返回错误信息
                return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'foods': []})


def meal_search_food_api(request):
    """
    添加餐食页面调用API搜索食物视图函数
    """
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET['q'].strip()
        if query:
            try:
                import json
                import logging
                import requests
                from django.conf import settings
                
                # 设置日志记录
                logger = logging.getLogger(__name__)
                
                # 准备请求头和载荷
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.XFYUN_API_KEY}"
                }
                
                prompt = f"请告诉我{query}这种食物每100克的营养成分，包括热量（千卡）、蛋白质（克）、碳水化合物（克）和脂肪（克）。以JSON格式返回结果，格式如下：{{\"name\": \"{query}\", \"calories\": 数值, \"protein\": 数值, \"carbs\": 数值, \"fat\": 数值}}。只返回JSON，不要其他内容。"
                
                payload = {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "model": "lite",  # 使用lite模型
                    "stream": False
                }

                # 发送请求
                response = requests.post(
                    settings.XFYUN_API_URL, 
                    json=payload, 
                    headers=headers, 
                    timeout=120
                )
                response.raise_for_status()

                content = response.json()['choices'][0]['message']['content'].strip()
                logger.info(f"API返回原始内容: {content}")
                
                # 处理可能的代码块格式
                if content.startswith("```json"):
                    content = content[7:]  # 移除 ```json
                if content.endswith('```'):
                    content = content[:-3]  # 移除 ```
                
                # 解析JSON
                try:
                    api_result = json.loads(content)
                    # 添加一个标记表示这是来自API的食物
                    api_result['from_api'] = True
                    return JsonResponse({'success': True, 'food': api_result})
                except json.JSONDecodeError:
                    # 如果解析失败，记录原始内容
                    logger.error(f"JSON解析失败，原始内容: {content}")
                    return JsonResponse({'success': False, 'error': 'API返回数据格式错误'}, status=500)
                
            except Exception as e:
                # 出错时记录日志
                logger.error(f"AI服务调用出现错误: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': '查询参数错误'})


def save_meal(request):
    """
    保存餐食记录视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        try:
            # 获取各餐的食物数据
            import json
            from django.urls import reverse
            from datetime import datetime
            
            breakfast_foods = request.POST.get('breakfast_foods', '[]')
            lunch_foods = request.POST.get('lunch_foods', '[]')
            dinner_foods = request.POST.get('dinner_foods', '[]')
            snack_foods = request.POST.get('snack_foods', '[]')
            selected_date = request.POST.get('selected_date', '')
            
            # 解析JSON数据
            breakfast_foods = json.loads(breakfast_foods)
            lunch_foods = json.loads(lunch_foods)
            dinner_foods = json.loads(dinner_foods)
            snack_foods = json.loads(snack_foods)
            
            # 获取数据库连接
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 插入餐食记录
            meal_types = {
                'breakfast': breakfast_foods,
                'lunch': lunch_foods,
                'dinner': dinner_foods,
                'snack': snack_foods
            }
            
            # 映射meal_type到数据库中的枚举值
            meal_type_mapping = {
                'breakfast': 'Breakfast',
                'lunch': 'Lunch',
                'dinner': 'Dinner',
                'snack': 'Snack'
            }
            
            inserted_count = 0  # 记录插入的记录数
            
            for meal_type, foods in meal_types.items():
                if foods:  # 只有当有食物时才创建记录
                    for food in foods:
                        # 检查是否来自API的食物（字符串ID且以api_开头，或者id为0且有from_api标记）
                        food_id = food['id']
                        if ((isinstance(food_id, str) and food_id.startswith('api_')) or \
                           (food_id == 0 or food_id == '0')) and food.get('from_api', False):
                            # 插入新食物到foods表
                            cursor.execute("""
                                INSERT INTO foods (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g) 
                                VALUES (%s, %s, %s, %s, %s)
                            """, (food['name'], food['calories'], food['protein'], food['carbs'], food['fat']))
                            
                            # 获取新插入的食物ID
                            food_id = cursor.lastrowid
                        elif isinstance(food_id, str) and food_id.startswith('api_') and not food.get('from_api', False):
                            # 如果是API食物但没有from_api标记，则跳过
                            continue
                        
                        # 构造recorded_at值
                        if selected_date:
                            recorded_at = selected_date + ' ' + datetime.now().strftime('%H:%M:%S')
                        else:
                            recorded_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 确保food_id是整数类型
                        if isinstance(food_id, str) and food_id.isdigit():
                            food_id = int(food_id)
                        
                        # 插入meal_records记录
                        sql = """
                            INSERT INTO meal_records (user_id, food_id, meal_type, serving_size, 
                                                     calories_consumed, recorded_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(sql, (
                            user_id,
                            food_id,
                            meal_type_mapping[meal_type],
                            food['quantity'],
                            food['calories'] * food['quantity'] / 100,
                            recorded_at
                        ))
                        
                        inserted_count += 1
            
            connection.commit()
            cursor.close()
            connection.close()
            
            if inserted_count > 0:
                messages.success(request, f'成功保存{inserted_count}条餐食记录')
            else:
                messages.info(request, '没有需要保存的餐食记录')
            
            # 保存成功后重定向到对应日期的页面
            if selected_date:
                return redirect(f"{reverse('FoodApp:add_meal')}?date={selected_date}")
            else:
                return redirect('FoodApp:add_meal')
            
        except Exception as e:
            messages.error(request, f'保存失败: {str(e)}')
            return redirect('FoodApp:add_meal')
    
    return redirect('FoodApp:add_meal')

def nutrition_analysis(request):
    """
    营养成分分析视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    # 获取查询日期，默认为今天
    import datetime
    import json
    selected_date = request.GET.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    
    try:
        # 获取数据库连接
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 查询指定日期的营养数据
        sql = """
            SELECT 
                mr.id,
                mr.meal_type,
                mr.serving_size,
                mr.calories_consumed,
                mr.recorded_at,
                f.name as food_name,
                f.protein_per_100g,
                f.carbs_per_100g,
                f.fat_per_100g,
                f.id as food_id
            FROM meal_records mr
            LEFT JOIN foods f ON mr.food_id = f.id
            WHERE mr.user_id = %s AND DATE(mr.recorded_at) = %s
            ORDER BY mr.meal_type, mr.recorded_at
        """
        cursor.execute(sql, (user_id, selected_date))
        records = cursor.fetchall()
        
        # 处理营养数据
        nutrition_data = {
            'total_calories': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0,
            'meals': {
                'breakfast': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'foods': []},
                'lunch': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'foods': []},
                'dinner': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'foods': []},
                'snack': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'foods': []}
            }
        }
        
        # 为每条记录计算营养成分
        for record in records:
            meal_type = record['meal_type'].lower()
            serving_size = float(record['serving_size']) if record['serving_size'] else 0
            calories = float(record['calories_consumed']) if record['calories_consumed'] else 0
            
            # 添加到对应餐次
            nutrition_data['meals'][meal_type]['calories'] += calories
            nutrition_data['meals'][meal_type]['foods'].append(record)
            
            # 累加总营养
            nutrition_data['total_calories'] += calories
            
            # 计算其他营养成分
            if record['protein_per_100g'] and record['carbs_per_100g'] and record['fat_per_100g']:
                protein_per_100g = float(record['protein_per_100g'])
                carbs_per_100g = float(record['carbs_per_100g'])
                fat_per_100g = float(record['fat_per_100g'])
                
                # 计算实际摄入的营养成分
                protein = protein_per_100g * serving_size / 100
                carbs = carbs_per_100g * serving_size / 100
                fat = fat_per_100g * serving_size / 100
                
                # 累加到餐次和总计
                nutrition_data['meals'][meal_type]['protein'] += protein
                nutrition_data['meals'][meal_type]['carbs'] += carbs
                nutrition_data['meals'][meal_type]['fat'] += fat
                
                nutrition_data['total_protein'] += protein
                nutrition_data['total_carbs'] += carbs
                nutrition_data['total_fat'] += fat
        
        # 准备图表数据
        # 1. 营养成分分布数据
        nutrients_data = {
            'labels': ['蛋白质', '碳水化合物', '脂肪'],
            'values': [
                round(nutrition_data['total_protein'], 1),
                round(nutrition_data['total_carbs'], 1),
                round(nutrition_data['total_fat'], 1)
            ]
        }
        
        # 2. 各餐次热量分布数据
        meal_calories_data = {
            'labels': ['早餐', '午餐', '晚餐', '加餐'],
            'values': [
                round(nutrition_data['meals']['breakfast']['calories'], 1),
                round(nutrition_data['meals']['lunch']['calories'], 1),
                round(nutrition_data['meals']['dinner']['calories'], 1),
                round(nutrition_data['meals']['snack']['calories'], 1)
            ]
        }
        
        # 3. 各餐次营养成分分布数据
        meal_nutrients_data = {
            'labels': ['早餐', '午餐', '晚餐', '加餐'],
            'protein': [
                round(nutrition_data['meals']['breakfast']['protein'], 1),
                round(nutrition_data['meals']['lunch']['protein'], 1),
                round(nutrition_data['meals']['dinner']['protein'], 1),
                round(nutrition_data['meals']['snack']['protein'], 1)
            ],
            'carbs': [
                round(nutrition_data['meals']['breakfast']['carbs'], 1),
                round(nutrition_data['meals']['lunch']['carbs'], 1),
                round(nutrition_data['meals']['dinner']['carbs'], 1),
                round(nutrition_data['meals']['snack']['carbs'], 1)
            ],
            'fat': [
                round(nutrition_data['meals']['breakfast']['fat'], 1),
                round(nutrition_data['meals']['lunch']['fat'], 1),
                round(nutrition_data['meals']['dinner']['fat'], 1),
                round(nutrition_data['meals']['snack']['fat'], 1)
            ]
        }
        
        # 4. 食物热量贡献数据（前5个贡献最高的食物）
        foods_calories_data = {
            'labels': [],
            'values': []
        }
        
        # 收集所有食物及其热量
        food_calories_map = {}
        for meal_type, meal_data in nutrition_data['meals'].items():
            for food in meal_data['foods']:
                food_name = food['food_name']
                calories = float(food['calories_consumed']) if food['calories_consumed'] else 0
                if food_name in food_calories_map:
                    food_calories_map[food_name] += calories
                else:
                    food_calories_map[food_name] = calories
        
        # 按热量排序并取前5个
        sorted_foods = sorted(food_calories_map.items(), key=lambda x: x[1], reverse=True)[:5]
        for food_name, calories in sorted_foods:
            foods_calories_data['labels'].append(food_name)
            foods_calories_data['values'].append(round(calories, 1))
        
        # 组合所有图表数据
        chart_data = {
            'nutrients': nutrients_data,
            'meal_calories': meal_calories_data,
            'meal_nutrients': meal_nutrients_data,
            'foods_calories': foods_calories_data
        }
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'数据查询出错: {str(e)}')
        nutrition_data = None
        chart_data = None
    
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'avatar': request.session.get('avatar_html'),  # 从session中获取头像HTML
        'selected_date': selected_date,
        'nutrition_data': nutrition_data,
        'chart_data': json.dumps(chart_data) if chart_data else None
    }
    return render(request, 'FoodApp/nutrition_analysis.html', context)

def calorie_calculator(request):
    """
    卡路里计算器视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    
    context = {
        'user_id': user_id,
        'username': username,
    }
    return render(request, 'FoodApp/calorie_calculator.html', context)

def diet_charts(request):
    """
    饮食图表统计视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    # 获取查询日期范围，默认为最近7天
    import datetime
    end_date = request.GET.get('end_date', datetime.date.today().strftime('%Y-%m-%d'))
    start_date = request.GET.get('start_date', 
                                (datetime.date.today() - datetime.timedelta(days=6)).strftime('%Y-%m-%d'))
    
    try:
        # 获取数据库连接
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 查询指定日期范围的饮食数据
        sql = """
            SELECT 
                DATE(mr.recorded_at) as date,
                mr.meal_type,
                mr.calories_consumed,
                f.name as food_name,
                f.category as food_category
            FROM meal_records mr
            LEFT JOIN foods f ON mr.food_id = f.id
            WHERE mr.user_id = %s AND DATE(mr.recorded_at) BETWEEN %s AND %s
            ORDER BY mr.recorded_at
        """
        cursor.execute(sql, (user_id, start_date, end_date))
        records = cursor.fetchall()
        
        # 处理图表数据
        chart_data = {
            'dates': [],
            'daily_calories': [],
            'avg_calories': 0,
            'total_days': 0,
            'most_consumed_food': '暂无数据',
            'nutrients': {
                'avg_protein': 0,
                'avg_carbs': 0,
                'avg_fat': 0
            },
            'meal_distribution': {
                'breakfast': 0,
                'lunch': 0,
                'dinner': 0,
                'snack': 0
            },
            'food_categories': []
        }
        
        if records:
            # 按日期分组数据
            from collections import defaultdict
            daily_data = defaultdict(lambda: {
                'calories': 0,
                'meals': defaultdict(int),
                'foods': defaultdict(int),
                'categories': defaultdict(int)
            })
            
            # 统计营养数据
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            nutrient_count = 0
            
            for record in records:
                date = record['date'].strftime('%Y-%m-%d')
                calories = float(record['calories_consumed']) if record['calories_consumed'] else 0
                meal_type = record['meal_type'].lower() if record['meal_type'] else 'snack'
                food_name = record['food_name'] if record['food_name'] else '未知食物'
                food_category = record['food_category'] if record['food_category'] else '其他'
                
                # 累加每日数据
                daily_data[date]['calories'] += calories
                daily_data[date]['meals'][meal_type] += calories
                daily_data[date]['foods'][food_name] += 1
                daily_data[date]['categories'][food_category] += 1
                
                # 统计营养数据（这里使用模拟数据，实际应用中应从数据库获取）
                if nutrient_count < 10:  # 限制查询次数
                    nutrient_sql = """
                        SELECT protein_per_100g, carbs_per_100g, fat_per_100g
                        FROM foods 
                        WHERE id = %s
                    """
                    cursor.execute(nutrient_sql, (record['food_id'],))
                    nutrient_data = cursor.fetchone()
                    
                    if nutrient_data:
                        # 这里简化处理，实际应该根据食物分量计算
                        total_protein += float(nutrient_data['protein_per_100g'] or 0)
                        total_carbs += float(nutrient_data['carbs_per_100g'] or 0)
                        total_fat += float(nutrient_data['fat_per_100g'] or 0)
                        nutrient_count += 1
            
            # 准备图表数据
            dates = sorted(daily_data.keys())
            chart_data['dates'] = dates
            chart_data['daily_calories'] = [daily_data[date]['calories'] for date in dates]
            chart_data['avg_calories'] = round(sum(chart_data['daily_calories']) / len(chart_data['daily_calories']), 0) if chart_data['daily_calories'] else 0
            chart_data['total_days'] = len(dates)
            
            # 计算各餐分布
            for date in dates:
                for meal_type, calories in daily_data[date]['meals'].items():
                    chart_data['meal_distribution'][meal_type] += calories
            
            # 计算平均营养摄入
            if nutrient_count > 0:
                chart_data['nutrients']['avg_protein'] = round(total_protein / nutrient_count, 1)
                chart_data['nutrients']['avg_carbs'] = round(total_carbs / nutrient_count, 1)
                chart_data['nutrients']['avg_fat'] = round(total_fat / nutrient_count, 1)
            
            # 找出最常摄入的食物
            all_foods = defaultdict(int)
            for date in dates:
                for food, count in daily_data[date]['foods'].items():
                    all_foods[food] += count
            
            if all_foods:
                chart_data['most_consumed_food'] = max(all_foods, key=all_foods.get)
            
            # 食物类别统计
            all_categories = defaultdict(int)
            for date in dates:
                for category, count in daily_data[date]['categories'].items():
                    all_categories[category] += count
            
            chart_data['food_categories'] = [
                {'category': category, 'count': count} 
                for category, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True)[:6]
            ]
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'数据查询出错: {str(e)}')
        chart_data = None
    
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'start_date': start_date,
        'end_date': end_date,
        'chart_data': chart_data,
    }
    return render(request, 'FoodApp/diet_charts.html', context)

def food_image_recognition(request):
    """
    食物图片识别视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    # 初始化识别结果
    top_results = []
    
    if request.method == 'POST' and request.FILES.get('food_image'):
        try:
            # 获取上传的图片文件
            food_image = request.FILES['food_image']
            
            # 检查文件类型
            if not food_image.content_type.startswith('image/'):
                messages.error(request, '请上传有效的图片文件')
                return render(request, 'FoodApp/food_image_recognition.html', {
                    'user_id': user_id,
                    'username': request.session.get('username'),
                    'avatar': request.session.get('avatar_html'),
                })
            
            # 检查文件大小（限制为5MB）
            if food_image.size > 5 * 1024 * 1024:
                messages.error(request, '图片文件大小不能超过5MB')
                return render(request, 'FoodApp/food_image_recognition.html', {
                    'user_id': user_id,
                    'username': request.session.get('username'),
                    'avatar': request.session.get('avatar_html'),
                })
            
            # 读取图片文件内容并转换为base64编码
            image_data = food_image.read()
            import base64
            img_base64 = base64.b64encode(image_data)
            
            # 调用百度API进行食物识别
            import requests
            
            # 百度API配置
            request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v2/dish"
            access_token = '24.e79a10837efd9b83217bf7ab7b34cc51.2592000.1757688481.282335-119765408'
            
            # 构造请求参数
            params = {
                "image": img_base64,
                "top_num": 5
            }
            
            request_url = request_url + "?access_token=" + access_token
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            
            # 发送请求到百度API
            response = requests.post(request_url, data=params, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(result)
                # 解析识别结果
                if 'result' in result and result['result']:
                    dish_results = result['result']
                    if dish_results:
                        # 获取置信度排名前三的识别结果
                        top_results_list = []
                        for i, dish in enumerate(dish_results[:3]):  # 取前三名
                            top_results_list.append({
                                'rank': i + 1,
                                'food_name': dish.get('name', '未知'),
                                'confidence': float(dish.get('probability', 0)) * 100,
                                'calorie': dish.get('calorie', '未知'),
                                'has_calorie': dish.get('has_calorie', False)
                            })
                        top_results = top_results_list
                        
                        # 显示成功消息
                        messages.success(request, '食物识别成功！')
                    else:
                        messages.error(request, '未能识别出食物，请尝试其他图片')
                else:
                    messages.error(request, '食物识别失败，请稍后重试')
            else:
                messages.error(request, f'API调用失败，状态码: {response.status_code}')
            
        except Exception as e:
            messages.error(request, f'图片上传或识别失败: {str(e)}')
    
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'avatar': request.session.get('avatar_html'),
        'top_results': top_results,
    }
    return render(request, 'FoodApp/food_image_recognition.html', context)


def meal_suggestion(request):
    """
    个性化餐食建议视图函数
    基于用户目标、心情、运动量等数据提供餐食建议
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 获取用户基本信息和目标
        cursor.execute("""
            SELECT u.*, g.goal_type, g.target_weight, g.daily_calorie_goal
            FROM users u
            LEFT JOIN goals g ON u.id = g.user_id
            WHERE u.id = %s
        """, (user_id,))
        user_info = cursor.fetchone()
        
        if not user_info:
            messages.error(request, '用户信息不存在')
            cursor.close()
            connection.close()
            return redirect('FoodApp:index')
        
        # 获取用户今天的饮食记录
        today = datetime.now().date()
        cursor.execute("""
            SELECT meal_type, SUM(calories_consumed) as total_calories
            FROM meal_records
            WHERE user_id = %s AND DATE(recorded_at) = %s
            GROUP BY meal_type
        """, (user_id, today))
        daily_meals = cursor.fetchall()

        # 获取用户最近的体重记录（使用用户表中的当前体重）
        # 注意：数据库中没有progress_records表，所以使用users表中的weight字段
        
        cursor.close()
        connection.close()
        
        # 处理表单提交
        if request.method == 'POST':
            mood = request.POST.get('mood', '')
            meal_type = request.POST.get('meal_type', '')
            additional_info = request.POST.get('additional_info', '')
            
            # 构建AI提示词
            prompt = f"""
            你是一个专业的营养师，需要根据以下用户信息为用户的一餐提供个性化建议：

            用户基本信息：
            - 年龄：{user_info['age'] or '未知'}岁
            - 性别：{user_info['gender'] or '未知'}
            - 身高：{user_info['height'] or '未知'}cm
            - 体重：{user_info['weight'] or '未知'}kg
            - 活动水平：{user_info['activity_level'] or '未知'}
            
            用户目标：
            - 目标类型：{user_info['goal_type'] or '未知'}
            - 目标体重：{user_info['target_weight'] or '未知'}kg
            - 每日热量目标：{user_info['daily_calorie_goal'] or '未知'}卡路里
            
            今日饮食情况：
            """
            
            total_calories_consumed = 0
            for meal in daily_meals:
                prompt += f"- {meal['meal_type']}: {meal['total_calories'] or 0}卡路里\n"
                total_calories_consumed += meal['total_calories'] or 0
                
            prompt += f"\n当前请求：\n"
            prompt += f"- 餐次类型：{meal_type}\n"
            prompt += f"- 用户心情：{mood}\n"
            prompt += f"- 附加信息：{additional_info}\n"
            prompt += f"- 今日已摄入热量：{total_calories_consumed}卡路里\n"
            
            prompt += """
            请根据以上信息，为用户推荐适合的餐食建议。请严格按照以下JSON格式返回结果，不要包含任何其他内容或格式标记：

            {
                "meals": [
                    {
                        "name": "推荐的餐食名称，例如：燕麦早餐",
                        "foods": [
                            {
                                "name": "具体食物名称，例如：燕麦片",
                                "amount": "食物分量，例如：100g",
                                "calories": 389
                            },
                            {
                                "name": "具体食物名称，例如：牛奶",
                                "amount": "食物分量，例如：200ml",
                                "calories": 160
                            }
                        ],
                        "total_calories": 549,
                        "nutritional_info": "营养分析，例如：这份早餐提供了丰富的膳食纤维和优质蛋白质，有助于维持饱腹感"
                    }
                ],
                "tips": [
                    "健康小贴士，例如：坚果富含不饱和脂肪酸，但热量较高，建议适量食用"
                ],
                "warnings": [
                    "注意事项，例如：如果您有乳糖不耐受，请将牛奶替换为豆浆或其他植物奶"
                ]
            }

            要求：
            1. 回答使用中文
            2. 内容专业但易懂
            3. 建议要具体可行
            4. meals数组至少包含1个元素，最多包含3个元素
            5. 每个meal中的foods数组至少包含2个元素，最多包含6个元素
            6. 每种食物必须包含具体的名称、分量和卡路里数
            7. 每餐的总卡路里数需要准确计算并提供
            8. 只返回JSON格式的数据，不要包含任何解释或其他文字
            9. 不要使用Markdown代码块格式（如```json）
            10. 确保返回的是有效的JSON格式
            11. 所有字段都必须包含具体内容，不能留空
            """
            
            try:
                import requests
                import json
                from django.conf import settings
                
                # 准备请求头和载荷
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.XFYUN_API_KEY}"
                }
                
                payload = {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "model": "lite",  # 使用lite模型
                    "stream": False
                }

                # 发送请求
                response = requests.post(
                    settings.XFYUN_API_URL, 
                    json=payload, 
                    headers=headers, 
                    timeout=120
                )
                response.raise_for_status()

                content = response.json()['choices'][0]['message']['content'].strip()

                if content.startswith("```json"):
                    content = content[7:]  # 移除 ```json
                if content.endswith('```'):
                    content = content[:-3]  # 移除 ```
                
                if content:
                    # 尝试解析JSON
                    try:
                        suggestion_data = json.loads(content)
                        # 将AI响应存储在session中，以便在模板中使用
                        request.session['meal_suggestion'] = suggestion_data
                        messages.success(request, '已生成个性化餐食建议')
                    except json.JSONDecodeError:
                        # 如果解析失败，将原始内容作为字符串存储
                        request.session['meal_suggestion'] = {
                            'meals': [{
                                'name': '默认餐食',
                                'foods': [{
                                    'name': '食物信息',
                                    'amount': '100g',
                                    'calories': 0
                                }],
                                'total_calories': 0,
                                'nutritional_info': content
                            }]
                        }
                        messages.success(request, '已生成个性化餐食建议')
                else:
                    messages.error(request, '生成餐食建议失败，请稍后重试')
                    
            except Exception as e:
                messages.error(request, f'AI服务调用失败: {str(e)}')
        
        # 从session中获取AI建议（如果存在）
        ai_suggestion = request.session.pop('meal_suggestion', None)
        
    except Exception as e:
        messages.error(request, f'数据查询出错: {str(e)}')
        return redirect('FoodApp:index')
    
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'avatar': request.session.get('avatar_html'),
        'user_info': user_info,
        'daily_meals': daily_meals,
        'suggestion': ai_suggestion,
    }
    
    return render(request, 'FoodApp/meal_suggestion.html', context)


def groups(request):
    """
    群组列表页面视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 获取用户创建的群组
        cursor.execute("""
            SELECT g.*, u.username as creator_name, 
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
            FROM vgroups g
            JOIN users u ON g.created_by = u.id
            WHERE g.created_by = %s
            ORDER BY g.created_at DESC
        """, (user_id,))
        created_groups = cursor.fetchall()
        
        # 获取用户加入的群组（作为成员）
        cursor.execute("""
            SELECT g.*, u.username as creator_name, 
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
            FROM vgroups g
            JOIN users u ON g.created_by = u.id
            JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_id = %s AND g.created_by != %s
            ORDER BY g.created_at DESC
        """, (user_id, user_id))
        joined_groups = cursor.fetchall()
        
        # 获取所有群组（排除用户已加入的）
        cursor.execute("""
            SELECT g.*, u.username as creator_name,
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
            FROM vgroups g
            JOIN users u ON g.created_by = u.id
            WHERE g.id NOT IN (
                SELECT gm.group_id FROM group_members gm WHERE gm.user_id = %s
                UNION
                SELECT g.id FROM vgroups g WHERE g.created_by = %s
            )
            ORDER BY g.created_at DESC
        """, (user_id, user_id))
        groups = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'获取挑战详情失败: {str(e)}')
        context = {
            'user_id': user_id,
            'username': request.session.get('username'),
            'avatar': request.session.get('avatar_html'),
            'challenge': None,
            'participants': [],
            'participant_count': 0,
            'user_challenge': None,
            'all_checkins': [],
        }
        return render(request, 'FoodApp/groups.html', context)

    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'avatar': request.session.get('avatar_html'),  # 从session中获取头像HTML
        'created_groups': created_groups,
        'joined_groups': joined_groups,
        'groups': groups,
    }
    return render(request, 'FoodApp/groups.html', context)


def create_group(request):
    """
    创建群组视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        group_name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not group_name:
            messages.error(request, '群组名称不能为空')
            return render(request, 'FoodApp/create_group.html', {
                'user_id': user_id,
                'username': request.session.get('username'),
            })
        
        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 创建群组
            cursor.execute("""
                INSERT INTO vgroups (group_name, description, created_by)
                VALUES (%s, %s, %s)
            """, (group_name, description, user_id))
            
            group_id = cursor.lastrowid
            
            # 将创建者添加为管理员
            cursor.execute("""
                INSERT INTO group_members (group_id, user_id, role)
                VALUES (%s, %s, 'Admin')
            """, (group_id, user_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messages.success(request, '群组创建成功')
            return redirect('FoodApp:groups')
            
        except Exception as e:
            messages.error(request, f'创建群组失败: {str(e)}')
    
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
    }
    return render(request, 'FoodApp/create_group.html', context)


def group_detail(request, group_id):
    """
    群组详情页面视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 检查用户是否是群组成员
        cursor.execute("""
            SELECT COUNT(*) as count FROM group_members 
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        is_member = cursor.fetchone()['count'] > 0
        
        if not is_member:
            messages.error(request, '您不是该群组的成员')
            return redirect('FoodApp:groups')
        
        # 获取群组信息
        cursor.execute("""
            SELECT g.*, u.username as creator_name
            FROM vgroups g
            JOIN users u ON g.created_by = u.id
            WHERE g.id = %s
        """, (group_id,))
        group = cursor.fetchone()
        
        if not group:
            messages.error(request, '群组不存在')
            return redirect('FoodApp:groups')
        
        # 获取群组成员
        cursor.execute("""
            SELECT gm.*, u.username, u.avatar
            FROM group_members gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id = %s
            ORDER BY gm.role DESC, gm.joined_at ASC
        """, (group_id,))
        members = cursor.fetchall()
        
        # 获取正在进行的挑战
        cursor.execute("""
            SELECT gc.*, u.username as creator_name,
                   (SELECT COUNT(*) FROM challenge_participants WHERE challenge_id = gc.id) as participant_count
            FROM group_challenges gc
            JOIN users u ON gc.created_by = u.id
            WHERE gc.group_id = %s AND gc.end_date >= CURDATE()
            ORDER BY gc.created_at DESC
        """, (group_id,))
        active_challenges = cursor.fetchall()
        
        # 获取最近的群组消息
        cursor.execute("""
            SELECT gm.*, u.username, u.avatar
            FROM group_messages gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id = %s
            ORDER BY gm.created_at DESC
            LIMIT 20
        """, (group_id,))
        messages_list = list(cursor.fetchall())
        
        # 反转消息顺序，使最新消息显示在底部
        messages_list.reverse()
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'获取群组信息失败: {str(e)}')
        return redirect('FoodApp:groups')
    
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'group': group,
        'members': members,
        'active_challenges': active_challenges,
        'messages_list': messages_list,
        'avatar': request.session.get('avatar_html'),
    }
    return render(request, 'FoodApp/group_detail.html', context)


def join_group(request, group_id):
    """
    加入群组视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 检查群组是否存在
        cursor.execute("SELECT id FROM vgroups WHERE id = %s", (group_id,))
        group = cursor.fetchone()
        
        if not group:
            messages.error(request, '群组不存在')
            cursor.close()
            connection.close()
            return redirect('FoodApp:groups')
        
        # 检查用户是否已经是成员
        cursor.execute("""
            SELECT COUNT(*) as count FROM group_members 
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        is_member = cursor.fetchone()['count'] > 0
        
        if is_member:
            messages.info(request, '您已经是该群组的成员')
        else:
            # 添加用户到群组
            cursor.execute("""
                INSERT INTO group_members (group_id, user_id)
                VALUES (%s, %s)
            """, (group_id, user_id))
            connection.commit()
            messages.success(request, '成功加入群组')
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'加入群组失败: {str(e)}')
    
    return redirect('FoodApp:group_detail', group_id=group_id)


def leave_group(request, group_id):
    """
    离开群组视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '请先登录'})
        else:
            messages.error(request, '请先登录')
            return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 检查用户是否是群组成员
        cursor.execute("""
            SELECT role FROM group_members 
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        member = cursor.fetchone()
        
        if not member:
            cursor.close()
            connection.close()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': '您不是该群组的成员'})
            else:
                messages.error(request, '您不是该群组的成员')
                return redirect('FoodApp:groups')
        
        # 检查用户是否是群组创建者
        cursor.execute("SELECT created_by FROM vgroups WHERE id = %s", (group_id,))
        group = cursor.fetchone()
        
        if group and group['created_by'] == user_id:
            cursor.close()
            connection.close()
            return JsonResponse({'success': False, 'message': '群组创建者不能离开群组，请先删除群组'})
        else:
            # 从群组中移除用户
            cursor.execute("""
                DELETE FROM group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id))
            connection.commit()
            cursor.close()
            connection.close()
            
            messages.success(request, '已离开群组')
            return JsonResponse({'success': True, 'message': '成功退出'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'离开群组失败: {str(e)}'})


def create_challenge(request, group_id):
    """
    创建挑战视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 检查用户是否是群组成员
        cursor.execute("""
            SELECT COUNT(*) as count FROM group_members 
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        is_member = cursor.fetchone()['count'] > 0
        
        if not is_member:
            messages.error(request, '您不是该群组的成员')
            cursor.close()
            connection.close()
            return redirect('FoodApp:groups')
        
        # 获取群组信息
        cursor.execute("SELECT * FROM vgroups WHERE id = %s", (group_id,))
        group = cursor.fetchone()
        
        if not group:
            messages.error(request, '群组不存在')
            cursor.close()
            connection.close()
            return redirect('FoodApp:groups')
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'获取群组信息失败: {str(e)}')
        return redirect('FoodApp:groups')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        challenge_type = request.POST.get('challenge_type', '')
        target_value = request.POST.get('target_value', '')
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '')
        
        # 验证输入
        if not name or not challenge_type or not target_value or not start_date or not end_date:
            messages.error(request, '请填写所有必填字段')
            return render(request, 'FoodApp/create_challenge.html', {
                'user_id': user_id,
                'username': request.session.get('username'),
                'group': group,
                'group_id': group_id,
            })
        
        try:
            # 验证日期
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            if end_date_obj <= start_date_obj:
                messages.error(request, '结束日期必须晚于开始日期')
                return render(request, 'FoodApp/create_challenge.html', {
                    'user_id': user_id,
                    'username': request.session.get('username'),
                    'group': group,
                    'group_id': group_id,
                })
            
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 创建挑战
            cursor.execute("""
                INSERT INTO group_challenges 
                (group_id, challenge_name, description, start_date, end_date, challenge_type, target_value, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (group_id, name, description, start_date, end_date, challenge_type, target_value, user_id))
            connection.commit()
            messages.success(request, '挑战创建成功')
            
            cursor.close()
            connection.close()
            
            return redirect('FoodApp:group_detail', group_id=group_id)
            
        except Exception as e:
            messages.error(request, f'创建挑战失败: {str(e)}')
    
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'group': group,
        'group_id': group_id,
    }
    return render(request, 'FoodApp/create_challenge.html', context)


def diet_recommendations(request):
    pass


def update_group(request, group_id):
    """
    更新群组信息视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        group_name = request.POST.get('group_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not group_name:
            messages.error(request, '群组名称不能为空')
        else:
            try:
                connection = get_database_connection()
                cursor = connection.cursor()
                
                # 检查群组是否存在且用户是创建者
                cursor.execute("""
                    SELECT id FROM vgroups WHERE id = %s AND created_by = %s
                """, (group_id, user_id))
                group = cursor.fetchone()
                
                if not group:
                    messages.error(request, '群组不存在或您无权限编辑此群组')
                else:
                    # 更新群组信息
                    cursor.execute("""
                        UPDATE vgroups 
                        SET group_name = %s, description = %s 
                        WHERE id = %s
                    """, (group_name, description, group_id))
                    connection.commit()
                    messages.success(request, '群组信息更新成功')
                
                cursor.close()
                connection.close()
                
            except Exception as e:
                messages.error(request, f'更新群组失败: {str(e)}')
    
    return redirect('FoodApp:group_detail', group_id=group_id)


def remove_member(request, group_id, user_id):
    """
    移除群组成员视图函数
    """
    # 检查当前用户是否已登录
    current_user_id = request.session.get('user_id')
    if not current_user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 检查群组是否存在且当前用户是创建者
        cursor.execute("""
            SELECT id FROM vgroups WHERE id = %s AND created_by = %s
        """, (group_id, current_user_id))
        group = cursor.fetchone()
        
        if not group:
            messages.error(request, '群组不存在或您无权限执行此操作')
        else:
            # 不能移除群组创建者
            if int(user_id) == int(current_user_id):
                messages.error(request, '不能移除群组创建者')
            else:
                # 移除成员
                cursor.execute("""
                    DELETE FROM group_members 
                    WHERE group_id = %s AND user_id = %s
                """, (group_id, user_id))
                connection.commit()
                messages.success(request, '成员已移除')
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'移除成员失败: {str(e)}')
    
    return redirect('FoodApp:group_detail', group_id=group_id)


def make_admin(request, group_id, user_id):
    """
    设置群组管理员视图函数
    """
    # 检查当前用户是否已登录
    current_user_id = request.session.get('user_id')
    if not current_user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 检查群组是否存在且当前用户是创建者
        cursor.execute("""
            SELECT id FROM vgroups WHERE id = %s AND created_by = %s
        """, (group_id, current_user_id))
        group = cursor.fetchone()
        print(group)
        if not group:
            messages.error(request, '群组不存在或您无权限执行此操作')
        else:
            # 检查用户是否是群组成员
            cursor.execute("""
                SELECT COUNT(*) as count FROM group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id))
            is_member = cursor.fetchone()['count'] > 0
            
            if not is_member:
                messages.error(request, '该用户不是群组成员')
            else:
                # 设置为管理员（role = 1）
                cursor.execute("""
                    UPDATE group_members 
                    SET role = 1 
                    WHERE group_id = %s AND user_id = %s
                """, (group_id, user_id))
                connection.commit()
                messages.success(request, '已设置为管理员')
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'设置管理员失败: {str(e)}')
    
    return redirect('FoodApp:group_detail', group_id=group_id)


def create_health_challenge(request):
    """
    创建健康挑战视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            duration = request.POST.get('duration', '').strip()
            target_value = request.POST.get('target_value', '').strip()
            unit = request.POST.get('unit', '').strip()
            
            # 验证必填字段
            if not title or not description or not duration or not target_value or not unit:
                messages.error(request, '请填写所有必填字段')
                return redirect('FoodApp:health_challenges')
            
            # 验证数字字段
            try:
                duration = int(duration)
                target_value = float(target_value)
            except ValueError:
                messages.error(request, '挑战时长和目标值必须是数字')
                return redirect('FoodApp:health_challenges')
            
            # 计算开始和结束日期
            from datetime import datetime, timedelta
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=duration)
            
            # 保存到数据库
            connection = get_database_connection()
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO health_challenges (title, description, start_date, end_date, target_value, unit)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, start_date, end_date, target_value, unit))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messages.success(request, '健康挑战创建成功！')
            
        except Exception as e:
            messages.error(request, f'创建健康挑战失败: {str(e)}')
    
    return redirect('FoodApp:health_challenges')


def health_challenges(request):
    """
    健康挑战页面视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 获取所有正在进行的挑战，按参与人数排序
        cursor.execute("""
            SELECT hc.*, 
                   COUNT(uc.user_id) as participant_count
            FROM health_challenges hc
            LEFT JOIN user_challenges uc ON hc.id = uc.challenge_id
            WHERE hc.start_date <= CURDATE() AND hc.end_date >= CURDATE()
            GROUP BY hc.id
            ORDER BY participant_count DESC
        """)
        challenges = list(cursor.fetchall())
        
        cursor.close()
        connection.close()
        
        # 获取用户信息
        username = request.session.get('username')
        avatar_html = request.session.get('avatar_html', '')
        
        context = {
            'user_id': user_id,
            'username': username,
            'avatar': avatar_html,
            'challenges': challenges,
        }
        
    except Exception as e:
        messages.error(request, f'获取挑战数据失败: {str(e)}')
        context = {
            'user_id': user_id,
            'username': request.session.get('username'),
            'avatar': request.session.get('avatar_html'),
            'challenges': [],
        }
    
    return render(request, 'FoodApp/health_challenges.html', context)


def challenge_detail(request, challenge_id):
    """
    健康挑战详情页面视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 获取挑战详情
        cursor.execute("""
            SELECT * FROM health_challenges 
            WHERE id = %s
        """, (challenge_id,))
        challenge = cursor.fetchone()
        
        if not challenge:
            messages.error(request, '挑战不存在')
            cursor.close()
            connection.close()
            return redirect('FoodApp:health_challenges')
        
        # 获取参与该挑战的用户列表
        cursor.execute("""
            SELECT u.id, u.username, u.avatar
            FROM user_challenges uc
            JOIN users u ON uc.user_id = u.id
            WHERE uc.challenge_id = %s
        """, (challenge_id,))
        participants = list(cursor.fetchall())
        
        # 获取参与人数
        cursor.execute("""
            SELECT COUNT(*) as participant_count
            FROM user_challenges
            WHERE challenge_id = %s
        """, (challenge_id,))
        participant_count_result = cursor.fetchone()
        participant_count = participant_count_result['participant_count'] if participant_count_result else 0
        
        # 检查当前用户是否已参与挑战
        cursor.execute("""
            SELECT * FROM user_challenges 
            WHERE challenge_id = %s AND user_id = %s
        """, (challenge_id, user_id))
        user_challenge = cursor.fetchone()
        
        # 获取打卡记录
        cursor.execute("""
            SELECT cc.checkin_date, cc.note, u.username, u.avatar, u.id as user_id
            FROM challenge_checkins cc
            JOIN user_challenges uc ON cc.user_challenge_id = uc.id
            JOIN users u ON uc.user_id = u.id
            WHERE uc.challenge_id = %s
            ORDER BY cc.checkin_date DESC, u.username ASC
        """, (challenge_id,))
        all_checkins = list(cursor.fetchall())
        
        # 为头像路径添加前缀
        for checkin in all_checkins:
            if checkin['avatar']:
                # 判断是否为预设头像 (数字1-7)
                if checkin['avatar'].isdigit() and checkin['avatar'] in ['1', '2', '3', '4', '5', '6', '7']:
                    checkin['avatar'] = f'/media/avatars/{checkin["avatar"]}.png'
                # 判断是否为上传的图片头像(不是emoji头像)
                elif not checkin['avatar'].startswith('&#x'):
                    checkin['avatar'] = f'/media/avatars/{checkin["avatar"]}'
                # emoji头像或其他情况使用默认头像
                else:
                    checkin['avatar'] = '/media/avatars/1.png'
            else:
                # 没有头像时使用默认头像
                checkin['avatar'] = '/media/avatars/1.png'
        
        cursor.close()
        connection.close()
        
        # 获取用户信息
        username = request.session.get('username')
        avatar_html = request.session.get('avatar_html', '')
        
        context = {
            'user_id': user_id,
            'username': username,
            'avatar': avatar_html,
            'challenge': challenge,
            'participants': participants,
            'participant_count': participant_count,
            'user_challenge': user_challenge,
            'all_checkins': all_checkins,
        }
        
    except Exception as e:
        messages.error(request, f'获取挑战详情失败: {str(e)}')
        context = {
            'user_id': user_id,
            'username': request.session.get('username'),
            'avatar': request.session.get('avatar_html'),
            'challenge': None,
            'participants': [],
            'participant_count': 0,
            'user_challenge': None,
        }
    
    return render(request, 'FoodApp/challenge_detail.html', context)


def add_activity(request):
    """
    添加活动视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    # 获取用户信息
    username = request.session.get('username')
    avatar_html = request.session.get('avatar_html', '')
    
    if request.method == 'POST':
        # 处理添加活动的表单提交
        activity_type = request.POST.get('activity_type', '').strip()
        duration = request.POST.get('duration', '').strip()
        calories_burned = request.POST.get('calories_burned', '').strip()
        date = request.POST.get('date', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # 验证输入数据
        if not all([activity_type, duration, calories_burned, date]):
            messages.error(request, '请填写所有必填字段')
            return redirect('FoodApp:activity_diary')
        
        try:
            duration = int(duration)
            calories_burned = float(calories_burned)
            
            if duration <= 0 or calories_burned < 0:
                messages.error(request, '持续时间和消耗卡路里必须为正数')
                return redirect('FoodApp:activity_diary')
        except ValueError:
            messages.error(request, '持续时间和消耗卡路里必须为有效数字')
            return redirect('FoodApp:activity_diary')
        
        # 连接数据库并插入新活动
        connection = get_database_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO activity_diary 
                    (user_id, activity_type, duration, calories_burned, date, notes) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (user_id, activity_type, duration, calories_burned, date, notes))
                connection.commit()
                messages.success(request, '活动添加成功！')
        except Exception as e:
            connection.rollback()
            messages.error(request, f'添加活动失败: {str(e)}')
        finally:
            connection.close()

        return redirect('FoodApp:activity_diary')

    # GET请求 - 显示添加活动表单和最近的活动列表
    recent_activities = []
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            # 查询最近的5条活动记录
            sql = """
                SELECT * FROM activity_diary 
                WHERE user_id = %s 
                ORDER BY date DESC, created_at DESC 
                LIMIT 5
            """
            cursor.execute(sql, (user_id,))
            recent_activities = cursor.fetchall()
    except Exception as e:
        messages.error(request, f'获取活动记录失败: {str(e)}')
    finally:
        connection.close()
    
    context = {
        'user_id': user_id,
        'username': username,
        'avatar': avatar_html,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'FoodApp/add_activity.html', context)


def activity_diary(request):
    """
    活动日记页面视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    # 获取筛选日期参数
    selected_date = request.GET.get('date', '')
    
    # 获取用户信息
    username = request.session.get('username')
    avatar_html = request.session.get('avatar_html', '')
    
    # 获取活动记录
    activities = []
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            if selected_date:
                # 如果有筛选日期，只获取该日期的活动
                sql = """
                    SELECT * FROM activity_diary 
                    WHERE user_id = %s AND date = %s
                    ORDER BY created_at DESC
                """
                cursor.execute(sql, (user_id, selected_date))
            else:
                # 如果没有筛选日期，获取最近的活动
                sql = """
                    SELECT * FROM activity_diary 
                    WHERE user_id = %s
                    ORDER BY date DESC, created_at DESC
                    LIMIT 20
                """
                cursor.execute(sql, (user_id,))
            
            activities = cursor.fetchall()
    except Exception as e:
        messages.error(request, f'获取活动记录失败: {str(e)}')
    finally:
        connection.close()
    
    context = {
        'user_id': user_id,
        'username': username,
        'avatar': avatar_html,
        'activities': activities,
        'selected_date': selected_date,
    }
    
    return render(request, 'FoodApp/activity_diary.html', context)


def health_challenges(request):
    """
    健康挑战页面视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    # 获取用户信息
    username = request.session.get('username')
    avatar_html = request.session.get('avatar_html', '')
    
    # 获取健康挑战列表
    challenges = []
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT * FROM health_challenges 
                ORDER BY created_at DESC
            """
            cursor.execute(sql)
            challenges = cursor.fetchall()
    except Exception as e:
        messages.error(request, f'获取健康挑战列表失败: {str(e)}')
    finally:
        connection.close()
    
    context = {
        'user_id': user_id,
        'username': username,
        'avatar': avatar_html,
        'challenges': challenges,
    }
    
    return render(request, 'FoodApp/health_challenges.html', context)


def checkin_challenge(request, challenge_id):
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        try:
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 获取挑战信息
            cursor.execute("""
                SELECT hc.*
                FROM health_challenges hc
                WHERE hc.id = %s
            """, (challenge_id,))
            challenge = cursor.fetchone()
            
            if not challenge:
                messages.error(request, '挑战不存在')
                cursor.close()
                connection.close()
                return redirect('FoodApp:health_challenges')
            
            # 获取用户挑战信息
            cursor.execute("""
                SELECT * FROM user_challenges 
                WHERE challenge_id = %s AND user_id = %s
            """, (challenge_id, user_id))
            user_challenge = cursor.fetchone()
            
            if not user_challenge:
                messages.error(request, '您尚未参与此挑战')
                cursor.close()
                connection.close()
                return redirect('FoodApp:challenge_detail', challenge_id=challenge_id)
            
            # 检查今天是否已经打卡
            from datetime import date
            today = date.today().strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM challenge_checkins
                WHERE user_challenge_id = %s AND checkin_date = %s
            """, (user_challenge['id'], today))
            
            if cursor.fetchone()['count'] > 0:
                messages.info(request, '今日已打卡')
                cursor.close()
                connection.close()
                return redirect('FoodApp:challenge_detail', challenge_id=challenge_id)
            
            # 执行打卡，checkin_value固定为1
            note = request.POST.get('note', '').strip()
            
            cursor.execute("""
                INSERT INTO challenge_checkins 
                (user_challenge_id, checkin_date, checkin_value, note)
                VALUES (%s, %s, %s, %s)
            """, (user_challenge['id'], today, 1, note))
            
            # 更新用户挑战进度
            cursor.execute("""
                UPDATE user_challenges 
                SET progress = progress + %s
                WHERE id = %s
            """, (1, user_challenge['id']))
            
            connection.commit()
            messages.success(request, '打卡成功！')
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            messages.error(request, f'打卡失败: {str(e)}')
        
        return redirect('FoodApp:challenge_detail', challenge_id=challenge_id)
    
    # GET请求，显示挑战详情
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 获取挑战信息
        cursor.execute("""
            SELECT hc.*
            FROM health_challenges hc
            WHERE hc.id = %s
        """, (challenge_id,))
        challenge = cursor.fetchone()
        
        if not challenge:
            messages.error(request, '挑战不存在')
            cursor.close()
            connection.close()
            return redirect('FoodApp:health_challenges')
        
        # 获取用户挑战信息
        cursor.execute("""
            SELECT uc.*, u.username
            FROM user_challenges uc
            JOIN users u ON uc.user_id = u.id
            WHERE uc.challenge_id = %s AND uc.user_id = %s
        """, (challenge_id, user_id))
        user_challenge = cursor.fetchone()
        
        # 获取挑战参与人数
        cursor.execute("""
            SELECT COUNT(*) as participant_count
            FROM user_challenges
            WHERE challenge_id = %s
        """, (challenge_id,))
        
        # 获取参与该挑战的用户列表
        cursor.execute("""
            SELECT u.id, u.username, u.avatar 
            FROM user_challenges uc
            JOIN users u ON uc.user_id = u.id
            WHERE uc.challenge_id = %s
        """, (challenge_id,))
        participants = list(cursor.fetchall())

        participant_count = cursor.fetchone()['participant_count']
        
        # 检查用户今天是否已完成挑战
        today_completed = False

        today_progress = 0
        if user_challenge:
            from datetime import date
            today = date.today().strftime('%Y-%m-%d')
            
            # 获取用户今天的打卡记录
            cursor.execute("""
                SELECT SUM(checkin_value) as today_total
                FROM challenge_checkins
                WHERE user_challenge_id = %s AND checkin_date = %s
            """, (user_challenge['id'], today))
            
            today_record = cursor.fetchone()
            today_progress = float(today_record['today_total']) if today_record['today_total'] else 0
            
            # 检查今天是否达到目标
            if today_progress >= float(challenge['target_value']):
                today_completed = True
        
        # 处理筛选参数
        filter_date = request.GET.get('filter_date', '')
        filter_user = request.GET.get('filter_user', 'all')  # 'all' 或 'me'
        
        # 构建查询所有用户打卡记录的SQL
        base_query = """
            SELECT cc.checkin_date, cc.note, u.username, u.avatar, u.id as user_id
            FROM challenge_checkins cc
            JOIN user_challenges uc ON cc.user_challenge_id = uc.id
            JOIN users u ON uc.user_id = u.id
            WHERE uc.challenge_id = %s
        """
        
        params = [challenge_id]
        
        # 添加日期筛选
        if filter_date:
            base_query += " AND cc.checkin_date = %s"
            params.append(filter_date)
        
        # 添加用户筛选
        if filter_user == 'me':
            base_query += " AND uc.user_id = %s"
            params.append(user_id)
        
        # 添加排序
        base_query += " ORDER BY cc.checkin_date DESC, u.username ASC"
        
        # 执行查询
        cursor.execute(base_query, params)
        all_checkins = list(cursor.fetchall())
        
        # 为头像路径添加前缀
        for checkin in all_checkins:
            if checkin['avatar']:
                # 判断是否为预设头像 (数字1-7)
                if checkin['avatar'].isdigit() and checkin['avatar'] in ['1', '2', '3', '4', '5', '6', '7']:
                    checkin['avatar'] = f'/media/avatars/{checkin["avatar"]}.png'
                # 判断是否为上传的图片头像(不是emoji头像)
                elif not checkin['avatar'].startswith('&#x'):
                    checkin['avatar'] = f'/media/avatars/{checkin["avatar"]}'
                # emoji头像或其他情况使用默认头像
                else:
                    checkin['avatar'] = '/media/avatars/1.png'
            else:
                # 没有头像时使用默认头像
                checkin['avatar'] = '/media/avatars/1.png'
        
        cursor.close()
        connection.close()
        
        # 计算进度百分比
        progress_percentage = 0
        if user_challenge and challenge['target_value'] > 0:
            progress_percentage = (user_challenge['progress'] / challenge['target_value']) * 100
        
        context = {
            'user_id': user_id,
            'username': request.session.get('username'),
            'avatar': request.session.get('avatar_html'),
            'challenge': challenge,
            'user_challenge': user_challenge,
            'participant_count': participant_count,
            'all_checkins': all_checkins,
            'progress_percentage': progress_percentage,
            'filter_date': filter_date,
            'filter_user': filter_user,
            'today_completed': today_completed,
            'today_progress': today_progress,
        }
        
        return render(request, 'FoodApp/challenge_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'获取挑战详情失败: {str(e)}')
        return redirect('FoodApp:health_challenges')


def join_challenge(request, challenge_id):
    """
    参与挑战视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 获取挑战信息
        cursor.execute("""
            SELECT hc.*
            FROM health_challenges hc
            WHERE hc.id = %s
        """, (challenge_id,))
        challenge = cursor.fetchone()
        
        if not challenge:
            messages.error(request, '挑战不存在')
            cursor.close()
            connection.close()
            return redirect('FoodApp:health_challenges')
        
        # 检查用户是否已经参与挑战
        cursor.execute("""
            SELECT COUNT(*) as count FROM user_challenges 
            WHERE challenge_id = %s AND user_id = %s
        """, (challenge_id, user_id))
        is_participant = cursor.fetchone()['count'] > 0
        
        if is_participant:
            messages.info(request, '您已经参与了该挑战')
        else:
            # 添加用户到挑战参与者
            cursor.execute("""
                INSERT INTO user_challenges (challenge_id, user_id)
                VALUES (%s, %s)
            """, (challenge_id, user_id))
            connection.commit()
            messages.success(request, '成功参与挑战')
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        messages.error(request, f'参与挑战失败: {str(e)}')
        return redirect('FoodApp:health_challenges')
    
    return redirect('FoodApp:challenge_detail', challenge_id=challenge_id)


def profile(request):
    """
    个人主页视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            username = request.POST.get('username')
            email = request.POST.get('email')
            age = request.POST.get('age')
            height = request.POST.get('height')
            weight = request.POST.get('weight')
            # 获取数据库连接
            connection = get_database_connection()
            cursor = connection.cursor()
            # 更新用户基本信息
            if username or email:
                cursor.execute("""
                    UPDATE users 
                    SET username = COALESCE(%s, username), 
                        email = COALESCE(%s, email)
                    WHERE id = %s
                """, (username, email, user_id))
                
                # 如果用户名被修改，更新session中的用户名
                if username:
                    request.session['username'] = username
            # 更新个人身体信息
            if age or height or weight:
                # 先检查是否已存在个人身体信息记录
                cursor.execute("""
                    SELECT id FROM users WHERE id = %s
                """, (user_id,))
                profile_record = cursor.fetchone()
                
                if profile_record:
                    # 更新现有记录
                    cursor.execute("""
                        UPDATE users
                        SET age = COALESCE(%s, age),
                            height = COALESCE(%s, height),
                            weight = COALESCE(%s, weight)
                        WHERE user_id = %s
                    """, (age, height, weight, user_id))
                else:
                    # 插入新记录
                    cursor.execute("""
                        INSERT INTO users (id, age, height, weight)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, age, height, weight))
            connection.commit()
            cursor.close()
            connection.close()
            messages.success(request, '个人资料更新成功')
            return redirect('FoodApp:profile')
            
        except Exception as e:
            messages.error(request, f'更新个人资料失败: {str(e)}')
            return redirect('FoodApp:profile')
    
    try:
        # 获取数据库连接
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 获取用户信息
        cursor.execute("""
            SELECT id, username, email, full_name, age, gender, height, weight, activity_level, avatar, created_at, updated_at
            FROM users 
            WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        # 获取用户身体信息（从user_profiles表）
        cursor.execute("""
            SELECT age, gender, height, weight
            FROM users
            WHERE id = %s
        """, (user_id,))
        personal_info = cursor.fetchone()
        # 获取用户目标信息
        cursor.execute("""
            SELECT id, goal_type, target_weight, target_date, daily_calorie_goal 
            FROM goals 
            WHERE user_id = %s
        """, (user_id,))
        goals = cursor.fetchone()
        cursor.close()
        connection.close()
        context = {
            'user_id': user_id,
            'username': request.session.get('username'),
            'avatar': request.session.get('avatar_html'),  # 从session中获取头像HTML
            'user': user,
            'personal_info': personal_info,
            'goals': goals,
        }
        return render(request, 'FoodApp/profile.html', context)
        
    except Exception as e:
        messages.error(request, f'获取用户信息失败: {str(e)}')
        return redirect('FoodApp:index')


def send_group_message(request, group_id):
    """
    发送群组消息视图函数（AJAX）
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': '请先登录'})
    
    if request.method == 'POST':
        try:
            # 处理JSON数据或表单数据
            if request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
                message = data.get('message', '').strip()
            else:
                message = request.POST.get('message', '').strip()
            
            if not message:
                return JsonResponse({'success': False, 'message': '消息内容不能为空'})
            
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 检查用户是否是群组成员
            cursor.execute("""
                SELECT COUNT(*) as count FROM group_members 
                WHERE group_id = %s AND user_id = %s
            """, (group_id, user_id))
            is_member = cursor.fetchone()['count'] > 0
            
            if not is_member:
                cursor.close()
                connection.close()
                return JsonResponse({'success': False, 'message': '您不是该群组的成员'})
            
            # 插入消息
            cursor.execute("""
                INSERT INTO group_messages (group_id, user_id, message)
                VALUES (%s, %s, %s)
            """, (group_id, user_id, message))
            
            message_id = cursor.lastrowid
            
            # 获取消息详情（包括发送者信息）
            cursor.execute("""
                SELECT gm.id, gm.group_id, gm.user_id, gm.message, gm.created_at, u.username, u.avatar
                FROM group_messages gm
                JOIN users u ON gm.user_id = u.id
                WHERE gm.id = %s
            """, (message_id,))
            new_message = cursor.fetchone()
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # 格式化时间
            from datetime import datetime
            formatted_time = new_message['created_at'].strftime('%H:%M') if isinstance(new_message['created_at'], datetime) else str(new_message['created_at'])[:5]
            
            return JsonResponse({
                'success': True, 
                'message': new_message['message'],
                'username': new_message['username'],
                'time': formatted_time
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'发送消息失败: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': '无效的请求方法'})


def get_group_messages(request, group_id):
    """
    获取群组消息视图函数（AJAX）
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': '请先登录'})
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 检查用户是否是群组成员
        cursor.execute("""
            SELECT COUNT(*) as count FROM group_members 
            WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        is_member = cursor.fetchone()['count'] > 0
        
        if not is_member:
            cursor.close()
            connection.close()
            return JsonResponse({'success': False, 'error': '您不是该群组的成员'})
        
        # 获取最近的群组消息（按时间升序排列，以便最新消息在底部）
        cursor.execute("""
            SELECT gm.*, u.username, u.avatar
            FROM group_messages gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id = %s
            ORDER BY gm.created_at ASC
            LIMIT 20
        """, (group_id,))
        messages_list = list(cursor.fetchall())
        
        # 获取消息后不需要反转，因为已经是按时间升序排列
        # 最新消息会在底部显示，符合用户阅读习惯
        
        cursor.close()
        connection.close()
        
        return JsonResponse({'success': True, 'messages': messages_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'获取群组消息失败: {str(e)}'})


def change_password(request):
    import hashlib

    from django.shortcuts import render, redirect
    from django.contrib import messages
    """
    修改用户密码视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # 验证表单数据
            if not current_password or not new_password or not confirm_password:
                messages.error(request, '所有字段都是必填的')
                return redirect('FoodApp:profile')
            
            if new_password != confirm_password:
                messages.error(request, '新密码和确认密码不匹配')
                return redirect('FoodApp:profile')
            
            if len(new_password) < 6:
                messages.error(request, '密码长度至少为6位')
                return redirect('FoodApp:profile')
            
            # 获取数据库连接
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 获取当前用户信息（包括密码）
            cursor.execute("""
                SELECT password FROM users WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                messages.error(request, '用户不存在')
                cursor.close()
                connection.close()
                return redirect('FoodApp:profile')
            
            # 验证当前密码是否正确
            current_password_hash = hashlib.sha256(current_password.encode('utf-8')).hexdigest()
            if user['password'] != current_password_hash:
                messages.error(request, '当前密码不正确')
                cursor.close()
                connection.close()
                return redirect('FoodApp:profile')
            
            # 更新密码
            new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            cursor.execute("""
                UPDATE users 
                SET password = %s 
                WHERE id = %s
            """, (new_password_hash, user_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messages.success(request, '密码修改成功')
            return redirect('FoodApp:profile')
            
        except Exception as e:
            messages.error(request, f'修改密码失败: {str(e)}')
            return redirect('FoodApp:profile')
    
    # 如果不是POST请求，重定向到个人资料页面
    return redirect('FoodApp:profile')


def add_food(request):
    """
    添加新食物视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        try:
            # 获取食物信息
            name = request.POST.get('name')
            category = request.POST.get('category', '')
            calories_per_100g = request.POST.get('calories_per_100g')
            protein_per_100g = request.POST.get('protein_per_100g', 0) or 0
            carbs_per_100g = request.POST.get('carbs_per_100g', 0) or 0
            fat_per_100g = request.POST.get('fat_per_100g', 0) or 0
            
            if not name or not calories_per_100g:
                messages.error(request, '食物名称和热量不能为空')
                return redirect('FoodApp:add_food')
            
            # 获取数据库连接
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 插入新食物到foods表
            cursor.execute("""
                INSERT INTO foods (name, category, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, category, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messages.success(request, f'食物"{name}"添加成功')
            return redirect('FoodApp:add_food')
            
        except Exception as e:
            messages.error(request, f'添加食物失败: {str(e)}')
            return redirect('FoodApp:add_food')
    
    # GET请求显示添加食物页面
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'avatar': request.session.get('avatar_html'),
    }
    
    return render(request, 'FoodApp/add_food.html', context)

    
def add_meal(request):
    """
    添加餐食记录页面视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        try:
            # 获取餐食信息
            food_id = request.POST.get('food_id')
            quantity = request.POST.get('quantity')
            meal_time = request.POST.get('meal_time')
            date = request.POST.get('date', datetime.date.today())
            
            if not food_id or not quantity or not meal_time:
                messages.error(request, '请选择食物、输入数量并选择餐时')
                return redirect('FoodApp:add_meal')
            
            # 获取数据库连接
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 插入新餐食记录到meal_records表
            cursor.execute("""
                INSERT INTO meal_records (user_id, food_id, quantity, meal_time, date) 
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, food_id, quantity, meal_time, date))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messages.success(request, '餐食记录添加成功')
            return redirect('FoodApp:add_meal')
            
        except Exception as e:
            messages.error(request, f'添加餐食记录失败: {str(e)}')
            return redirect('FoodApp:add_meal')
    
    # GET请求显示添加餐食页面
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'avatar': request.session.get('avatar_html'),
    }
    
    return render(request, 'FoodApp/add_meal.html', context)


def delete_meal_record(request):
    """
    删除餐食记录视图函数
    """
    if request.method == 'POST':
        # 检查用户是否已登录
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, '请先登录')
            return redirect('FoodApp:login')
        
        try:
            record_id = request.POST.get('record_id')
            selected_date = request.POST.get('date')
            
            if not record_id:
                messages.error(request, '无效的记录ID')
                return redirect('FoodApp:nutrition_analysis')
            
            # 获取数据库连接
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 检查记录是否属于当前用户
            cursor.execute("""
                SELECT id FROM meal_records 
                WHERE id = %s AND user_id = %s
            """, (record_id, user_id))
            
            record = cursor.fetchone()
            if not record:
                messages.error(request, '找不到指定的餐食记录或您没有权限删除此记录')
                cursor.close()
                connection.close()
                return redirect('FoodApp:nutrition_analysis')
            
            # 删除记录
            cursor.execute("DELETE FROM meal_records WHERE id = %s AND user_id = %s", (record_id, user_id))
            connection.commit()
            cursor.close()
            connection.close()
            
            messages.success(request, '餐食记录已成功删除')
            
        except Exception as e:
            messages.error(request, f'删除餐食记录时出错: {str(e)}')

        return redirect('FoodApp:nutrition_analysis')
    
    # 如果不是POST请求，重定向到营养分析页面
    return redirect('FoodApp:nutrition_analysis')


def update_profile(request):
    """
    更新用户个人信息视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': '请先登录'})
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')

    # 处理头像上传
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            avatar_file = request.FILES['avatar']
            
            # 生成文件名
            file_extension = avatar_file.name.split('.')[-1]
            file_name = f"{user_id}_avatar_{int(time.time())}.{file_extension}"
            
            # 保存文件
            path = default_storage.save(f'avatars/{file_name}', ContentFile(avatar_file.read()))
            
            # 更新数据库中的头像信息
            connection = get_database_connection()
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET avatar = %s
                WHERE id = %s
            """, (file_name, user_id))
            connection.commit()
            cursor.close()
            connection.close()
            
            # 更新session中的头像信息
            request.session['avatar'] = file_name
            
            # 处理头像显示逻辑，直接传递给前端显示
            avatar_html = f'<img src="/media/avatars/{file_name}" alt="头像" class="user-avatar">'
            
            # 更新session中的头像HTML
            request.session['avatar_html'] = avatar_html
            
            # 如果是AJAX请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': '头像更新成功',
                    'avatar_url': f'/media/avatars/{file_name}'
                })
            
            messages.success(request, '头像更新成功')
            return redirect('FoodApp:profile')
            
        except Exception as e:
            error_message = f'头像上传失败: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_message})
            messages.error(request, error_message)
            return redirect('FoodApp:profile')
    
    # 处理个人信息更新
    elif request.method == 'POST':
        try:
            # 获取表单数据
            full_name = request.POST['full_name']
            email = request.POST['email']
            age = request.POST['age']
            gender = request.POST['gender']
            height = request.POST['height']
            weight = request.POST['weight']
            activity_level = request.POST['activity_level']
            
            # 获取数据库连接
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 更新用户信息
            cursor.execute("""
                UPDATE users 
                SET full_name = %s, email = %s, age = %s, gender = %s, height = %s, weight = %s, activity_level = %s
                WHERE id = %s
            """, (full_name, email, age, gender, height, weight, activity_level, user_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # 更新session中的头像HTML（如果头像信息有变化）
            avatar = request.session.get('avatar')
            if avatar:
                # 处理头像显示逻辑，直接传递给前端显示
                if avatar.isdigit():
                    # 预设头像 (1-7)
                    avatar_html = f'<img src="/media/avatars/{avatar}.png" alt="头像" class="user-avatar">'
                elif not avatar.startswith('&#x'):
                    # 上传的图片头像
                    avatar_html = f'<img src="/media/avatars/{avatar}" alt="头像" class="user-avatar">'
                else:
                    # emoji头像 - 使用默认头像1.png
                    avatar_html = '<img src="/media/avatars/1.png" alt="头像" class="user-avatar">'
                
                # 更新session中的头像HTML
                request.session['avatar_html'] = avatar_html
            
            messages.success(request, '个人信息更新成功')
            return redirect('FoodApp:profile')
            
        except Exception as e:
            messages.error(request, f'更新个人信息失败: {str(e)}')
            return redirect('FoodApp:profile')
    
    # 如果不是POST请求，重定向到个人资料页面
    return redirect('FoodApp:profile')


def create_plan(request):
    """
    创建用户健康计划视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            goal_type = request.POST['goal_type']
            target_weight = request.POST['target_weight']
            target_date = request.POST['target_date']
            daily_calorie_goal = request.POST['daily_calorie_goal']
            
            # 获取数据库连接
            connection = get_database_connection()
            cursor = connection.cursor()
            
            # 检查是否已存在目标
            cursor.execute("SELECT id FROM goals WHERE user_id = %s", (user_id,))
            existing_goal = cursor.fetchone()
            
            if existing_goal:
                # 更新现有目标
                cursor.execute("""
                    UPDATE goals 
                    SET goal_type = %s, target_weight = %s, target_date = %s, daily_calorie_goal = %s
                    WHERE user_id = %s
                """, (goal_type, target_weight, target_date, daily_calorie_goal, user_id))
            else:
                # 创建新目标
                cursor.execute("""
                    INSERT INTO goals (user_id, goal_type, target_weight, target_date, daily_calorie_goal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, goal_type, target_weight, target_date, daily_calorie_goal))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            messages.success(request, '健康计划创建成功')
            return redirect('FoodApp:profile')
            
        except Exception as e:
            messages.error(request, f'创建健康计划失败: {str(e)}')
            return redirect('FoodApp:profile')
    
    return redirect('FoodApp:profile')


def health_challenges(request):
    """
    健康挑战页面视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        
        # 获取所有正在进行的挑战，按参与人数排序
        cursor.execute("""
            SELECT hc.*, 
                   COUNT(uc.user_id) as participant_count
            FROM health_challenges hc
            LEFT JOIN user_challenges uc ON hc.id = uc.challenge_id
            WHERE hc.start_date <= CURDATE() AND hc.end_date >= CURDATE()
            GROUP BY hc.id
            ORDER BY participant_count DESC
        """)
        active_challenges = list(cursor.fetchall())
        
        # 获取所有已结束的挑战，按结束时间倒序排序
        cursor.execute("""
            SELECT hc.*, 
                   COUNT(uc.user_id) as participant_count
            FROM health_challenges hc
            LEFT JOIN user_challenges uc ON hc.id = uc.challenge_id
            WHERE hc.end_date < CURDATE()
            GROUP BY hc.id
            ORDER BY hc.end_date DESC
        """)
        ended_challenges = list(cursor.fetchall())
        
        cursor.close()
        connection.close()
        
        # 获取用户信息
        username = request.session.get('username')
        avatar_html = request.session.get('avatar_html', '')
        
        context = {
            'user_id': user_id,
            'username': username,
            'avatar': avatar_html,
            'challenges': active_challenges,
            'ended_challenges': ended_challenges,
        }
        
    except Exception as e:
        messages.error(request, f'获取挑战数据失败: {str(e)}')
        context = {
            'user_id': user_id,
            'username': request.session.get('username'),
            'avatar': request.session.get('avatar_html'),
            'challenges': [],
            'ended_challenges': [],
        }
    
    return render(request, 'FoodApp/health_challenges.html', context)


def recipe_suggestion(request):
    """
    食谱推荐和制作过程展示视图函数
    """
    # 检查用户是否已登录
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, '请先登录')
        return redirect('FoodApp:login')
    
    recipe_info = None
    recipe_name = ''
    
    # 处理GET请求中通过食物识别传递的dish_name参数
    if request.method == 'GET':
        recipe_name = request.GET.get('dish_name', '').strip()
    
    if request.method == 'POST':
        recipe_name = request.POST.get('recipe_name', '').strip()
        
        if not recipe_name:
            messages.error(request, '请输入菜品名称')
        else:
            try:
                # 构建AI提示词，请求食谱制作过程
                prompt = f"""
                你是一个专业的厨师，请提供"{recipe_name}"的详细制作过程。
                
                要求：
                1. 列出所需的食材和分量
                2. 提供详细的制作步骤
                3. 说明烹饪时间和技巧要点
                4. 提供营养价值简要分析
                5. 给出食用建议
                
                请严格按照以下JSON格式返回结果，不要包含任何其他内容，确保返回的是严格可解析的JSON：
                {{
                    "recipe_name": "{recipe_name}",
                    "ingredients": [
                        {{"name": "食材1", "amount": "分量1"}},
                        {{"name": "食材2", "amount": "分量2"}}
                    ],
                    "steps": [
                        "步骤1描述",
                        "步骤2描述"
                    ],
                    "cooking_time": "预计烹饪时间",
                    "tips": "烹饪技巧和要点",
                    "nutrition": "营养价值简要分析",
                    "serving_suggestions": "食用建议"
                }}
                
                重要说明：
                1. 请严格按照上述JSON格式返回，不要包含任何其他内容
                2. 不要使用任何Markdown格式，如``json
                3. 所有字段都必须是字符串类型
                4. 不要在JSON中使用中文引号，只使用英文引号(")
                5. ingredients字段是一个包含对象的数组
                6. steps字段是一个包含字符串的数组
                7. 确保返回的JSON格式完全正确，可以被标准JSON解析器解析
                8. 所有内容使用中文
                
                请用中文回答，内容要具体、实用，避免空泛的建议。
                """
                
                # 获取AI建议
                recipe_info_json = get_ai_meal_suggestion(prompt)
                
                # 将JSON字符串解析为Python对象

                print(recipe_info)
                import json
                try:
                    recipe_info = json.loads(recipe_info_json)
                except json.JSONDecodeError:
                    recipe_info = None
                    messages.error(request, '食谱信息解析失败，请稍后重试')
                    
            except Exception as e:
                messages.error(request, f'获取食谱信息失败: {str(e)}')
    
    context = {
        'user_id': user_id,
        'username': request.session.get('username'),
        'avatar': request.session.get('avatar_html'),
        'recipe_info': recipe_info,
        'recipe_name': recipe_name,
    }
    return render(request, 'FoodApp/recipe_suggestion.html', context)


def get_ai_meal_suggestion(prompt):
    """
    调用讯飞星火大模型API获取餐食建议
    """
    import json
    import logging
    import requests
    from django.conf import settings
    
    # 设置日志记录
    logger = logging.getLogger(__name__)
    
    # 定义默认错误处理函数
    def get_default_ai_meal_suggestion_with_error(error_message):
        """
        获取带错误信息的默认AI餐食建议
        """
        logger = logging.getLogger(__name__)
        logger.info(f"使用带错误信息的默认AI餐食建议: {error_message}")
        
        import json
        return json.dumps({
            "recipe_name": "默认食谱",
            "ingredients": [
                {"name": "燕麦粥", "amount": "100克"},
                {"name": "全麦面包", "amount": "2片"},
                {"name": "水煮蛋", "amount": "1个"}
            ],
            "steps": [
                "燕麦粥用牛奶或水煮制，可加入少量坚果增加口感",
                "全麦面包可轻微烘烤后食用",
                "水煮蛋煮制6-8分钟达到最佳口感"
            ],
            "cooking_time": "15分钟",
            "tips": "燕麦粥要不断搅拌防止粘锅，全麦面包不要烤焦，水煮蛋时间要掌握好",
            "nutrition": "均衡营养、适量蛋白质、复合碳水化合物",
            "serving_suggestions": "建议搭配新鲜水果一起食用，增加维生素摄入"
        }, ensure_ascii=False)
    
    try:
        # 准备请求头和载荷
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.XFYUN_API_KEY}"
        }
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "lite",  # 使用lite模型
            "stream": False
        }

        # 发送请求
        response = requests.post(settings.XFYUN_API_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        content = response.json()['choices'][0]['message']['content'].strip()
        logger.info(f"AI返回原始内容: {content}")
        
        # 如果是简单的热量查询，直接返回内容
        if "请告诉我" in prompt and "多少卡路里热量" in prompt:
            # 简单处理，返回纯文本内容
            return content

        # 处理可能的代码块格式
        if content.startswith("```json"):
            content = content[7:]  # 移除 ```json
        if content.endswith('```'):
            content = content[:-3]  # 移除 ```
            
        # 进一步清理内容，确保是有效的JSON
        # 移除可能的前缀或后缀文本
        start_index = content.find('{')
        end_index = content.rfind('}')
        
        if start_index != -1 and end_index != -1 and end_index > start_index:
            content = content[start_index:end_index+1]
            
        # 尝试解析JSON
        try:
            suggestion_data = json.loads(content)
            return json.dumps(suggestion_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
            # 如果解析失败，尝试查找第一个完整的JSON对象
            logger.warning(f"JSON解析失败，错误信息: {str(e)}，原始内容: {content}")
            
            # 尝试查找第一个完整的JSON对象
            try:
                # 查找第一个{和对应的最后一个}
                first_brace = content.find('{')
                if first_brace != -1:
                    # 从第一个{开始查找完整的JSON对象
                    brace_count = 0
                    for i in range(first_brace, len(content)):
                        if content[i] == '{':
                            brace_count += 1
                        elif content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                # 找到了匹配的结束括号
                                json_str = content[first_brace:i+1]
                                suggestion_data = json.loads(json_str)
                                return json.dumps(suggestion_data, ensure_ascii=False)
            except Exception as inner_e:
                logger.warning(f"尝试解析第一个JSON对象失败: {str(inner_e)}")
            
            # 如果所有方法都失败，返回默认建议
            return json.dumps(get_default_ai_meal_suggestion_with_error("JSON解析失败"), ensure_ascii=False)
        
    except Exception as e:
        # 出错时返回默认建议
        logger.error(f"AI服务调用出现错误: {str(e)}")
        return json.dumps(get_default_ai_meal_suggestion_with_error("系统错误，请稍后重试"), ensure_ascii=False)
