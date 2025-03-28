from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(20), unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    join_date = Column(DateTime, default=datetime.datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    stars = Column(Integer, default=0)
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_code = Column(String(20), unique=True, nullable=False)
    
    # Relationships
    referrals = relationship('User', backref='referrer', remote_side=[id])
    limits = relationship('UserLimit', back_populates='user', uselist=False, cascade='all, delete-orphan')
    transactions = relationship('Transaction', back_populates='user', cascade='all, delete-orphan')
    message_logs = relationship('MessageLog', back_populates='user', cascade='all, delete-orphan')
    subscriptions = relationship('Subscription', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(telegram_id='{self.telegram_id}', username='{self.username}')>"

class UserLimit(Base):
    __tablename__ = 'user_limits'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    text_messages_used = Column(Integer, default=0)
    text_messages_limit = Column(Integer, default=5)  # Default from env
    image_generations_used = Column(Integer, default=0)
    image_generations_limit = Column(Integer, default=1)  # Default from env
    voice_messages_used = Column(Integer, default=0)
    voice_messages_limit = Column(Integer, default=5)  # Same as text by default
    reset_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='limits')
    
    def __repr__(self):
        return f"<UserLimit(user_id='{self.user_id}', text_used='{self.text_messages_used}/{self.text_messages_limit}')>"

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Integer, nullable=False)  # Can be positive (purchase) or negative (usage)
    description = Column(String(255), nullable=True)
    transaction_date = Column(DateTime, default=datetime.datetime.utcnow)
    transaction_type = Column(String(50), nullable=False)  # 'purchase', 'usage', 'referral_reward', etc.
    
    # Relationships
    user = relationship('User', back_populates='transactions')
    
    def __repr__(self):
        return f"<Transaction(user_id='{self.user_id}', amount='{self.amount}', type='{self.transaction_type}')>"

class MessageLog(Base):
    __tablename__ = 'message_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'text', 'voice', 'image'
    user_message = Column(Text, nullable=True)
    bot_response = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='message_logs')
    
    def __repr__(self):
        return f"<MessageLog(user_id='{self.user_id}', type='{self.message_type}', timestamp='{self.timestamp}')>"

class StarPackage(Base):
    __tablename__ = 'star_packages'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    stars_amount = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Price in currency
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<StarPackage(name='{self.name}', stars='{self.stars_amount}', price='{self.price}')>"

class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    stars_cost = Column(Integer, nullable=False)
    duration_days = Column(Integer, nullable=False)  # Subscription duration in days
    daily_limit = Column(Integer, nullable=False)  # Daily message limit, -1 for unlimited
    plan_type = Column(String(20), nullable=False)  # 'text', 'image'
    is_active = Column(Boolean, default=True)
    
    # Relationships
    subscriptions = relationship('Subscription', back_populates='plan')
    
    def __repr__(self):
        return f"<SubscriptionPlan(name='{self.name}', type='{self.plan_type}', cost='{self.stars_cost}')>"

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan_id = Column(Integer, ForeignKey('subscription_plans.id'), nullable=False)
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', back_populates='subscriptions')
    plan = relationship('SubscriptionPlan', back_populates='subscriptions')
    
    def __repr__(self):
        return f"<Subscription(user_id='{self.user_id}', plan='{self.plan.name if self.plan else None}', end_date='{self.end_date}')>"

class AdminSettings(Base):
    __tablename__ = 'admin_settings'
    
    id = Column(Integer, primary_key=True)
    setting_name = Column(String(100), nullable=False, unique=True)
    setting_value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<AdminSettings(name='{self.setting_name}', value='{self.setting_value}')>"

class Advertisement(Base):
    __tablename__ = 'advertisements'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Advertisement(id='{self.id}', active='{self.is_active}')>"

class BroadcastMessage(Base):
    __tablename__ = 'broadcast_messages'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    sent_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    status = Column(String(20), default='pending')  # 'pending', 'in_progress', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<BroadcastMessage(id='{self.id}', status='{self.status}', sent='{self.sent_count}/{self.total_count}')>"
