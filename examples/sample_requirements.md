# 电商订单管理系统

## 项目概述

设计并实现一个基于微服务架构的电商订单管理系统，支持用户下单、订单处理、支付、库存管理等核心功能。

## 技术栈要求

- **后端框架**: SpringBoot 2.7.0
- **Java版本**: Java 8
- **数据库**: MySQL 8.0
- **ORM框架**: MyBatis Plus 3.5.0
- **服务注册发现**: Nacos 2.1.0
- **缓存**: Redis 6.0
- **消息队列**: RocketMQ 4.9.0

## 微服务架构设计

### 1. 用户服务 (user-service)
- **端口**: 8081
- **数据库**: ecommerce_user
- **职责**: 用户注册、登录、个人信息管理

#### 主要功能
- 用户注册
- 用户登录/登出
- 用户信息查询和修改
- 用户地址管理

#### 数据模型
```sql
-- 用户表
CREATE TABLE sys_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    status TINYINT DEFAULT 1, -- 1:正常 0:禁用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 用户地址表
CREATE TABLE user_address (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    receiver_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    province VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    district VARCHAR(50) NOT NULL,
    detail_address VARCHAR(200) NOT NULL,
    is_default TINYINT DEFAULT 0, -- 1:默认地址 0:非默认
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
);
```

### 2. 商品服务 (product-service)
- **端口**: 8082
- **数据库**: ecommerce_product
- **职责**: 商品信息管理、库存管理

#### 主要功能
- 商品信息查询
- 商品分类管理
- 库存查询和扣减
- 商品搜索

#### 数据模型
```sql
-- 商品表
CREATE TABLE product (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    category_id BIGINT NOT NULL,
    brand VARCHAR(100),
    status TINYINT DEFAULT 1, -- 1:上架 0:下架
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category_id (category_id),
    INDEX idx_status (status)
);

-- 商品分类表
CREATE TABLE product_category (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    parent_id BIGINT DEFAULT 0,
    sort_order INT DEFAULT 0,
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 订单服务 (order-service)
- **端口**: 8083
- **数据库**: ecommerce_order
- **职责**: 订单创建、订单状态管理、订单查询

#### 主要功能
- 创建订单
- 订单状态管理
- 订单查询
- 订单取消

#### 数据模型
```sql
-- 订单主表
CREATE TABLE order_master (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status TINYINT NOT NULL, -- 1:待支付 2:已支付 3:已发货 4:已完成 5:已取消
    receiver_name VARCHAR(50) NOT NULL,
    receiver_phone VARCHAR(20) NOT NULL,
    receiver_address VARCHAR(300) NOT NULL,
    remark VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_order_no (order_no),
    INDEX idx_status (status)
);

-- 订单明细表
CREATE TABLE order_detail (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order_id (order_id)
);
```

### 4. 支付服务 (payment-service)
- **端口**: 8084
- **数据库**: ecommerce_payment
- **职责**: 支付处理、支付记录管理

#### 主要功能
- 创建支付订单
- 支付回调处理
- 支付状态查询
- 退款处理

#### 数据模型
```sql
-- 支付记录表
CREATE TABLE payment_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    payment_no VARCHAR(50) UNIQUE NOT NULL,
    order_no VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method TINYINT NOT NULL, -- 1:支付宝 2:微信 3:银行卡
    status TINYINT NOT NULL, -- 1:待支付 2:支付成功 3:支付失败 4:已退款
    third_party_no VARCHAR(100), -- 第三方支付流水号
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_order_no (order_no),
    INDEX idx_payment_no (payment_no),
    INDEX idx_user_id (user_id)
);
```

## 服务间调用关系

### API接口设计

#### 用户服务接口
```
GET  /api/user/profile/{userId}           # 获取用户信息
POST /api/user/login                      # 用户登录
POST /api/user/register                   # 用户注册
PUT  /api/user/profile                    # 更新用户信息
GET  /api/user/addresses/{userId}         # 获取用户地址列表
POST /api/user/address                    # 添加用户地址
```

#### 商品服务接口
```
GET  /api/product/{productId}             # 获取商品详情
GET  /api/product/list                    # 获取商品列表
POST /api/product/stock/check             # 检查库存
PUT  /api/product/stock/deduct            # 扣减库存
PUT  /api/product/stock/restore           # 恢复库存
```

#### 订单服务接口
```
POST /api/order/create                    # 创建订单
GET  /api/order/{orderId}                 # 获取订单详情
GET  /api/order/user/{userId}             # 获取用户订单列表
PUT  /api/order/status                    # 更新订单状态
PUT  /api/order/cancel/{orderId}          # 取消订单
```

#### 支付服务接口
```
POST /api/payment/create                  # 创建支付订单
POST /api/payment/callback                # 支付回调
GET  /api/payment/status/{paymentNo}      # 查询支付状态
POST /api/payment/refund                  # 申请退款
```

### 服务调用流程

#### 下单流程
1. **用户下单**: 前端调用订单服务创建订单
2. **验证用户**: 订单服务调用用户服务验证用户信息
3. **检查库存**: 订单服务调用商品服务检查库存
4. **扣减库存**: 订单服务调用商品服务扣减库存
5. **创建订单**: 订单服务保存订单信息
6. **返回结果**: 返回订单创建结果

#### 支付流程
1. **发起支付**: 前端调用支付服务创建支付订单
2. **调用第三方**: 支付服务调用第三方支付接口
3. **支付回调**: 第三方支付回调支付服务
4. **更新订单**: 支付服务调用订单服务更新订单状态
5. **通知用户**: 发送支付成功通知

## 非功能性要求

### 性能要求
- 订单创建接口响应时间 < 500ms
- 商品查询接口响应时间 < 200ms
- 系统支持并发用户数 > 1000
- 数据库查询优化，合理使用索引

### 可靠性要求
- 系统可用性 ≥ 99.9%
- 支持服务降级和熔断
- 关键业务数据需要备份
- 支持事务一致性

### 安全性要求
- 用户密码加密存储
- API接口需要身份验证
- 敏感数据传输加密
- 防止SQL注入

## 部署和配置

### Nacos配置
```yaml
spring:
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848
        namespace: ecommerce
        group: DEFAULT_GROUP
```

### 数据库配置
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/{database_name}?useUnicode=true&characterEncoding=utf8&useSSL=false
    username: root
    password: password
    driver-class-name: com.mysql.cj.jdbc.Driver
```

### Redis配置
```yaml
spring:
  redis:
    host: localhost
    port: 6379
    database: 0
    timeout: 3000ms
```

## 开发规范

### 代码规范
- 使用统一的包命名规范: com.ecommerce.{service-name}
- Controller层负责参数校验和结果封装
- Service层负责业务逻辑处理
- Repository层负责数据访问

### 异常处理
- 统一异常处理机制
- 自定义业务异常
- 错误码规范化

### 日志规范
- 使用SLF4J + Logback
- 关键业务操作记录日志
- 统一日志格式

## 测试要求

### 单元测试
- 每个Service方法需要编写单元测试
- 测试覆盖率要求 > 80%
- 使用Mock框架模拟依赖

### 集成测试
- 测试服务间接口调用
- 测试数据库操作
- 测试异常场景处理

## 项目交付

### Git仓库结构
```
ecommerce-microservices/
├── user-service/
├── product-service/
├── order-service/
├── payment-service/
├── common/                    # 公共模块
├── docker-compose.yml         # 本地开发环境
├── README.md
└── docs/                      # 文档目录
```

### 文档要求
- API文档（Swagger）
- 数据库设计文档
- 部署文档
- 开发环境搭建文档 