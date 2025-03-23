import datetime
from sqlalchemy import and_, or_
from database.db import get_session
from database.models import User, Subscription, SubscriptionPlan, Transaction
from bot.services.telegram_stars_service import TelegramStarsService
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    @staticmethod
    async def get_all_subscription_plans(plan_type=None):
        """Get all available subscription plans"""
        session = get_session()
        try:
            query = session.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True)
            
            if plan_type:
                query = query.filter(SubscriptionPlan.plan_type == plan_type)
                
            plans = query.order_by(SubscriptionPlan.stars_cost).all()
            return plans
        finally:
            session.close()
    
    @staticmethod
    async def get_user_active_subscriptions(user_id, plan_type=None):
        """Get all active subscriptions for a user"""
        session = get_session()
        try:
            now = datetime.datetime.utcnow()
            query = session.query(Subscription).join(SubscriptionPlan).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.end_date > now
            )
            
            if plan_type:
                query = query.filter(SubscriptionPlan.plan_type == plan_type)
                
            subscriptions = query.all()
            return subscriptions
        finally:
            session.close()
    
    @staticmethod
    async def subscribe_user(user_id, plan_id, telegram_id=None):
        """Subscribe a user to a plan using Telegram Stars"""
        session = get_session()
        try:
            # Get the plan
            plan = session.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == plan_id,
                SubscriptionPlan.is_active == True
            ).first()
            
            if not plan:
                return False, "Plan not found or inactive"
            
            # Get the user
            user = session.query(User).get(user_id)
            if not user:
                return False, "User not found"
            
            # Check if Telegram Stars integration is enabled
            if telegram_id:
                # Try to check Telegram Stars balance
                try:
                    stars_balance = await TelegramStarsService.get_stars_balance(telegram_id)
                    if stars_balance and hasattr(stars_balance, 'balance'):
                        # If we have access to Telegram Stars balance
                        if stars_balance.balance < plan.stars_cost:
                            return False, "Not enough Telegram Stars"
                        
                        # Создаем инвойс для оплаты звездами Telegram
                        # Согласно документации, для цифровых товаров используем валюту XTR (Telegram Stars)
                        title = f"Подписка на план {plan.name}"
                        description = f"Подписка на {plan.duration_days} дней с лимитом {plan.daily_limit} сообщений в день"
                        
                        # В реальном приложении здесь должен быть вызов API для списания звезд
                        # Для полной интеграции нужно использовать sendInvoice с currency="XTR"
                        logger.info(f"Creating Telegram Stars invoice for subscription: {title}, {plan.stars_cost} stars")
                    else:
                        # Fall back to internal stars system
                        if user.stars < plan.stars_cost:
                            return False, "Not enough stars"
                        
                        # Deduct stars from internal system
                        user.stars -= plan.stars_cost
                except Exception as e:
                    logger.error(f"Error checking Telegram Stars balance: {str(e)}")
                    # Fall back to internal stars system
                    if user.stars < plan.stars_cost:
                        return False, "Not enough stars"
                    
                    # Deduct stars from internal system
                    user.stars -= plan.stars_cost
            else:
                # Use internal stars system
                if user.stars < plan.stars_cost:
                    return False, "Not enough stars"
                
                # Deduct stars from internal system
                user.stars -= plan.stars_cost
            
            # Calculate end date
            start_date = datetime.datetime.utcnow()
            end_date = start_date + datetime.timedelta(days=plan.duration_days)
            
            # Create subscription
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            
            # Record transaction
            transaction = Transaction(
                user_id=user_id,
                amount=-plan.stars_cost,
                description=f"Subscription to {plan.name} ({plan.plan_type})",
                transaction_type="subscription"
            )
            
            session.add_all([subscription, transaction])
            session.commit()
            
            return True, f"Successfully subscribed to {plan.name} until {end_date.strftime('%Y-%m-%d')}"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    async def check_subscription_limit(user_id, message_type):
        """Check if a user has an active subscription with available limits"""
        session = get_session()
        try:
            now = datetime.datetime.utcnow()
            
            # Determine plan type based on message type
            plan_type = 'text' if message_type in ['text', 'voice'] else 'image'
            
            # Get active subscriptions
            subscriptions = session.query(Subscription).join(SubscriptionPlan).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.end_date > now,
                SubscriptionPlan.plan_type == plan_type
            ).all()
            
            if not subscriptions:
                return False, 0, None
            
            # Find the best subscription (unlimited or highest daily limit)
            best_subscription = None
            best_limit = 0
            
            for sub in subscriptions:
                if sub.plan.daily_limit == -1:  # Unlimited
                    best_subscription = sub
                    best_limit = -1
                    break
                elif sub.plan.daily_limit > best_limit:
                    best_subscription = sub
                    best_limit = sub.plan.daily_limit
            
            if best_limit == -1:  # Unlimited
                return True, -1, best_subscription
            elif best_limit > 0:
                return True, best_limit, best_subscription
            else:
                return False, 0, None
        finally:
            session.close()
    
    @staticmethod
    async def process_telegram_stars_payment(user_id, telegram_id, plan_id, stars_amount):
        """Process a payment made with Telegram Stars
        
        This method should be called after a successful Telegram Stars payment
        to create the subscription for the user.
        
        Args:
            user_id: Database user ID
            telegram_id: Telegram user ID
            plan_id: Subscription plan ID
            stars_amount: Amount of stars paid
            
        Returns:
            tuple: (success, message)
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Processing Telegram Stars payment for user {user_id} (Telegram ID: {telegram_id}), plan {plan_id}, amount {stars_amount}")
        
        session = get_session()
        try:
            # Get the plan
            plan = session.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == plan_id,
                SubscriptionPlan.is_active == True
            ).first()
            
            if not plan:
                logger.error(f"Plan {plan_id} not found or inactive")
                return False, "План подписки не найден или неактивен"
            
            # Verify payment amount
            if stars_amount < plan.stars_cost:
                logger.error(f"Payment amount {stars_amount} is less than plan cost {plan.stars_cost}")
                return False, "Сумма платежа меньше стоимости плана"
            
            # Проверяем баланс Telegram Stars еще раз
            stars_balance = await TelegramStarsService.get_stars_balance(telegram_id)
            
            if not stars_balance or not hasattr(stars_balance, 'balance') or stars_balance.balance < plan.stars_cost:
                logger.error(f"Insufficient stars balance: {stars_balance.balance if stars_balance and hasattr(stars_balance, 'balance') else 'unknown'}, required: {plan.stars_cost}")
                return False, "Недостаточно звезд Telegram для оформления подписки"
            
            # Списываем звезды через Telegram Stars API
            deduction_result = await TelegramStarsService.deduct_stars(telegram_id, plan.stars_cost, f"Подписка на план {plan.name}")
            
            if not deduction_result or not deduction_result.get('success'):
                error_message = deduction_result.get('message', 'Неизвестная ошибка') if deduction_result else 'Не удалось списать звезды'
                logger.error(f"Error deducting stars: {error_message}")
                return False, f"Ошибка при списании звезд: {error_message}"
            
            # Calculate end date
            start_date = datetime.datetime.utcnow()
            end_date = start_date + datetime.timedelta(days=plan.duration_days)
            
            # Create subscription
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            
            # Record transaction
            transaction = Transaction(
                user_id=user_id,
                amount=-plan.stars_cost,
                description=f"Оплата звездами Telegram за {plan.name} ({plan.plan_type})",
                transaction_type="telegram_stars_subscription"
            )
            
            session.add_all([subscription, transaction])
            session.commit()
            
            logger.info(f"User {user_id} (Telegram ID: {telegram_id}) successfully subscribed to plan {plan.name} until {end_date.strftime('%Y-%m-%d')}")
            
            return True, f"Успешно подписаны на {plan.name} до {end_date.strftime('%d.%m.%Y')}"
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing Telegram Stars payment: {str(e)}")
            return False, f"Ошибка: {str(e)}"
        finally:
            session.close()

    @staticmethod
    async def initialize_subscription_plans():
        """Initialize default subscription plans or update existing ones"""
        session = get_session()
        try:
            # Define the plans we want to have
            text_plans = [
                {
                    "name": "Стартовый",
                    "description": "+20 сообщений в день\nСрок действия: 7 дней",
                    "stars_cost": 100,
                    "duration_days": 7,
                    "daily_limit": 20,
                    "plan_type": "text"
                },
                {
                    "name": "Продвинутый",
                    "description": "+50 сообщений в день\nСрок действия: 14 дней",
                    "stars_cost": 250,
                    "duration_days": 14,
                    "daily_limit": 50,
                    "plan_type": "text"
                },
                {
                    "name": "Супер",
                    "description": "Безлимитное количество сообщений\nСрок действия: 30 дней",
                    "stars_cost": 450,
                    "duration_days": 30,
                    "daily_limit": -1,  # Unlimited
                    "plan_type": "text"
                }
            ]
            
            image_plans = [
                {
                    "name": "Мини",
                    "description": "+5 картинок в день\nСрок действия: 7 дней",
                    "stars_cost": 80,
                    "duration_days": 7,
                    "daily_limit": 5,
                    "plan_type": "image"
                },
                {
                    "name": "Стандарт",
                    "description": "+15 картинок в день\nСрок действия: 14 дней",
                    "stars_cost": 180,
                    "duration_days": 14,
                    "daily_limit": 15,
                    "plan_type": "image"
                },
                {
                    "name": "Максимум",
                    "description": "+30 картинок в день\nСрок действия: 30 дней",
                    "stars_cost": 350,
                    "duration_days": 30,
                    "daily_limit": 30,
                    "plan_type": "image"
                }
            ]
            
            all_plans = text_plans + image_plans
            
            # Check if we already have plans
            existing_plans = session.query(SubscriptionPlan).all()
            
            if not existing_plans:
                # Create all plans
                for plan_data in all_plans:
                    plan = SubscriptionPlan(
                        name=plan_data["name"],
                        description=plan_data["description"],
                        stars_cost=plan_data["stars_cost"],
                        duration_days=plan_data["duration_days"],
                        daily_limit=plan_data["daily_limit"],
                        plan_type=plan_data["plan_type"],
                        is_active=True
                    )
                    session.add(plan)
            else:
                # Update existing plans or create new ones
                existing_plan_names = {(p.name, p.plan_type): p for p in existing_plans}
                
                for plan_data in all_plans:
                    key = (plan_data["name"], plan_data["plan_type"])
                    if key in existing_plan_names:
                        # Update existing plan
                        plan = existing_plan_names[key]
                        plan.description = plan_data["description"]
                        plan.stars_cost = plan_data["stars_cost"]
                        plan.duration_days = plan_data["duration_days"]
                        plan.daily_limit = plan_data["daily_limit"]
                        plan.is_active = True
                    else:
                        # Create new plan
                        plan = SubscriptionPlan(
                            name=plan_data["name"],
                            description=plan_data["description"],
                            stars_cost=plan_data["stars_cost"],
                            duration_days=plan_data["duration_days"],
                            daily_limit=plan_data["daily_limit"],
                            plan_type=plan_data["plan_type"],
                            is_active=True
                        )
                        session.add(plan)
            
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error initializing subscription plans: {str(e)}")
        finally:
            session.close()
