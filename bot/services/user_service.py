import datetime
import random
import string
import logging
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from database.db import get_session
from database.models import User, UserLimit, Transaction, MessageLog
from config.config import FREE_TEXT_MESSAGES_LIMIT, FREE_IMAGE_GENERATION_LIMIT, FREE_VOICE_MESSAGES_LIMIT, REFERRAL_REWARD_STARS, DAILY_FREE_MESSAGES
from bot.utils.session_utils import session_scope, with_session

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    @with_session
    async def get_or_create_user_id(telegram_id, username=None, first_name=None, last_name=None, session=None):
        """Get an existing user ID or create a new user and return its ID"""
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            
            if not user:
                # Generate a unique referral code
                referral_code = UserService._generate_referral_code()
                
                # Create a new user
                user = User(
                    telegram_id=str(telegram_id),
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    referral_code=referral_code
                )
                session.add(user)
                session.flush()  # Flush to get the user ID
                
                # Get free message limits from admin settings
                from bot.services.admin_service import AdminService
                free_text_messages = int(await AdminService.get_setting('FREE_TEXT_MESSAGES_LIMIT', FREE_TEXT_MESSAGES_LIMIT))
                free_image_generations = int(await AdminService.get_setting('FREE_IMAGE_GENERATION_LIMIT', FREE_IMAGE_GENERATION_LIMIT))
                
                # Create user limits
                user_limits = UserLimit(
                    user_id=user.id,
                    text_messages_limit=free_text_messages,
                    image_generations_limit=free_image_generations,
                    voice_messages_limit=FREE_VOICE_MESSAGES_LIMIT
                )
                session.add(user_limits)
                session.commit()
                return user.id
            else:
                # Update user information if changed
                if username and user.username != username:
                    user.username = username
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                
                # Update last activity
                user.last_activity = datetime.datetime.utcnow()
                
                # Get the user ID before closing the session
                user_id = user.id
                session.commit()
                return user_id
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None, session=None):
        """Get an existing user or create a new one"""
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            
            if not user:
                # Generate a unique referral code
                referral_code = UserService._generate_referral_code()
                
                # Create a new user
                user = User(
                    telegram_id=str(telegram_id),
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    referral_code=referral_code
                )
                session.add(user)
                session.flush()  # Flush to get the user ID
                
                # Create user limits
                user_limits = UserLimit(
                    user_id=user.id,
                    text_messages_limit=FREE_TEXT_MESSAGES_LIMIT,
                    image_generations_limit=FREE_IMAGE_GENERATION_LIMIT,
                    voice_messages_limit=FREE_VOICE_MESSAGES_LIMIT
                )
                session.add(user_limits)
                session.commit()
            else:
                # Update user information if changed
                if username and user.username != username:
                    user.username = username
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                
                # Update last activity
                user.last_activity = datetime.datetime.utcnow()
                session.commit()
            
            return user
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    def _generate_referral_code(length=8):
        """Generate a unique referral code"""
        with session_scope() as session:
            while True:
                # Generate a random code
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
                
                # Check if the code already exists
                existing = session.query(User).filter(User.referral_code == code).first()
                if not existing:
                    return code
    
    @staticmethod
    @with_session
    async def process_referral(user_id, referral_code, session=None):
        """Process a referral and reward both users"""
        if not referral_code:
            return False
        
        try:
            # Get the referrer user
            referrer = session.query(User).filter(User.referral_code == referral_code).first()
            if not referrer or referrer.id == user_id:
                return False
            
            # Get the referred user
            user = session.query(User).get(user_id)
            if not user or user.referrer_id:
                return False  # User already has a referrer
            
            # Update the referred user
            user.referrer_id = referrer.id
            
            # Add stars to both users
            user.stars += REFERRAL_REWARD_STARS
            referrer.stars += REFERRAL_REWARD_STARS
            
            # Record transactions
            user_transaction = Transaction(
                user_id=user.id,
                amount=REFERRAL_REWARD_STARS,
                description=f"Referral bonus for using code {referral_code}",
                transaction_type="referral_reward"
            )
            
            referrer_transaction = Transaction(
                user_id=referrer.id,
                amount=REFERRAL_REWARD_STARS,
                description=f"Referral bonus for user {user.telegram_id} using your code",
                transaction_type="referral_reward"
            )
            
            session.add_all([user_transaction, referrer_transaction])
            session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def check_user_limits(user_id, message_type, session=None):
        """Check if a user has reached their limits"""
        from bot.services.subscription_service import SubscriptionService
        
        # First, check if the user has an active subscription
        has_subscription, subscription_limit, _ = await SubscriptionService.check_subscription_limit(user_id, message_type)
        
        # If user has an unlimited subscription, return immediately
        if has_subscription and subscription_limit == -1:
            return True, -1
        
        try:
            user_limits = session.query(UserLimit).filter(UserLimit.user_id == user_id).first()
            
            if not user_limits:
                return False, 0
            
            # Check if we need to reset daily limits
            today = datetime.datetime.utcnow().date()
            reset_date = user_limits.reset_date.date()
            
            if reset_date < today:
                # Reset daily limits
                user_limits.text_messages_used = 0
                user_limits.image_generations_used = 0
                user_limits.voice_messages_used = 0
                user_limits.reset_date = datetime.datetime.utcnow()
            
            # Check limits based on message type
            if message_type == 'text':
                # Calculate total limit (free + subscription)
                total_limit = user_limits.text_messages_limit
                if has_subscription:
                    total_limit += subscription_limit
                
                has_free_limit = user_limits.text_messages_used < total_limit
                remaining = total_limit - user_limits.text_messages_used
            elif message_type == 'image':
                # Calculate total limit (free + subscription)
                total_limit = user_limits.image_generations_limit
                if has_subscription:
                    total_limit += subscription_limit
                
                has_free_limit = user_limits.image_generations_used < total_limit
                remaining = total_limit - user_limits.image_generations_used
            elif message_type == 'voice':
                # Calculate total limit (free + subscription)
                total_limit = user_limits.voice_messages_limit
                if has_subscription:
                    total_limit += subscription_limit
                
                has_free_limit = user_limits.voice_messages_used < total_limit
                remaining = total_limit - user_limits.voice_messages_used
            else:
                return False, 0
            
            session.commit()
            return has_free_limit, max(0, remaining)
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def update_user_usage(user_id, message_type, session=None):
        """Update user usage after processing a message"""
        try:
            user_limits = session.query(UserLimit).filter(UserLimit.user_id == user_id).first()
            
            if not user_limits:
                return
            
            # Update usage based on message type
            if message_type == 'text':
                user_limits.text_messages_used += 1
            elif message_type == 'image':
                user_limits.image_generations_used += 1
            elif message_type == 'voice':
                user_limits.voice_messages_used += 1
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def log_message(user_id, message_type, user_message, bot_response, tokens_used=0, session=None):
        """Log a message exchange"""
        try:
            message_log = MessageLog(
                user_id=user_id,
                message_type=message_type,
                user_message=user_message,
                bot_response=bot_response,
                tokens_used=tokens_used
            )
            
            session.add(message_log)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def get_user_stars(user_id, session=None):
        """Get the number of stars a user has"""
        try:
            user = session.query(User).get(user_id)
            if user is not None:
                session.expunge(user)
            return user.stars if user else 0
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def use_stars(user_id, amount, description, session=None):
        """Use stars for a service"""
        try:
            user = session.query(User).get(user_id)
            
            if not user or user.stars < amount:
                return False
            
            # Deduct stars
            user.stars -= amount
            
            # Record transaction
            transaction = Transaction(
                user_id=user_id,
                amount=-amount,
                description=description,
                transaction_type="usage"
            )
            
            session.add(transaction)
            session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def add_stars(user_id, amount, description, transaction_type="purchase", session=None):
        """Add stars to a user's account"""
        try:
            user = session.query(User).get(user_id)
            
            if not user:
                return False
            
            # Add stars
            user.stars += amount
            
            # Record transaction
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                description=description,
                transaction_type=transaction_type
            )
            
            session.add(transaction)
            session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def get_user_limits(user_id, session=None):
        """Get a user's current limits and usage"""
        try:
            user_limits = session.query(UserLimit).filter(UserLimit.user_id == user_id).first()
            
            if not user_limits:
                return None
            
            # Check if we need to reset daily limits
            today = datetime.datetime.utcnow().date()
            reset_date = user_limits.reset_date.date()
            
            if reset_date < today:
                # Reset daily limits
                user_limits.text_messages_used = 0
                user_limits.image_generations_used = 0
                user_limits.voice_messages_used = 0
                user_limits.reset_date = datetime.datetime.utcnow()
                session.commit()
            
            return user_limits
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    async def get_user_limits_as_dict(user_id, session=None):
        """Get a user's current limits and usage as a dictionary to avoid DetachedInstanceError"""
        try:
            # Create a session if not provided
            close_session = False
            if not session:
                session = get_session()
                close_session = True
                
            user_limits = session.query(UserLimit).filter(UserLimit.user_id == user_id).first()
            
            # Default values if no limits found
            result = {
                'text_messages_limit': 0,
                'text_messages_used': 0,
                'image_generations_limit': 0,
                'image_generations_used': 0,
                'voice_messages_limit': 0,
                'voice_messages_used': 0,
                'reset_date': datetime.datetime.utcnow()
            }
            
            if user_limits:
                # Check if we need to reset daily limits
                today = datetime.datetime.utcnow().date()
                reset_date = user_limits.reset_date.date()
                
                if reset_date < today:
                    # Reset daily limits
                    user_limits.text_messages_used = 0
                    user_limits.image_generations_used = 0
                    user_limits.voice_messages_used = 0
                    user_limits.reset_date = datetime.datetime.utcnow()
                    session.commit()
                
                # Convert ORM object to dictionary
                result = {
                    'text_messages_limit': user_limits.text_messages_limit,
                    'text_messages_used': user_limits.text_messages_used,
                    'image_generations_limit': user_limits.image_generations_limit,
                    'image_generations_used': user_limits.image_generations_used,
                    'voice_messages_limit': user_limits.voice_messages_limit,
                    'voice_messages_used': user_limits.voice_messages_used,
                    'reset_date': user_limits.reset_date
                }
            
            return result
        except Exception as e:
            logger.error(f"Error getting user limits as dict: {str(e)}")
            # Return default values in case of error
            return {
                'text_messages_limit': 0,
                'text_messages_used': 0,
                'image_generations_limit': 0,
                'image_generations_used': 0,
                'voice_messages_limit': 0,
                'voice_messages_used': 0,
                'reset_date': datetime.datetime.utcnow()
            }
        finally:
            if close_session:
                session.close()

    @staticmethod
    @with_session
    async def get_user_stats(session=None):
        """Get user statistics for admin panel"""
        try:
            total_users = session.query(func.count(User.id)).scalar()
            active_users = session.query(func.count(User.id)).filter(
                User.last_activity >= datetime.datetime.utcnow() - datetime.timedelta(days=7),
                User.is_active == True,
                User.is_blocked == False
            ).scalar()
            blocked_users = session.query(func.count(User.id)).filter(User.is_blocked == True).scalar()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "blocked_users": blocked_users
            }
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def get_user_by_telegram_id(telegram_id, session=None):
        """Get a user by their Telegram ID"""
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            return user
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def add_stars(user_id, amount, session=None):
        """Add stars to a user's account"""
        try:
            user = session.query(User).get(user_id)
            
            if not user:
                return False
            
            # Add stars
            user.stars += amount
            
            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                amount=amount,
                description=f"Admin added {amount} stars",
                transaction_type="admin_add"
            )
            
            session.add(transaction)
            session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def reset_user_limits(user_id, session=None):
        """Reset a user's daily limits"""
        try:
            user_limits = session.query(UserLimit).filter(UserLimit.user_id == user_id).first()
            
            if not user_limits:
                return False
            
            # Reset limits
            user_limits.text_messages_used = 0
            user_limits.image_generations_used = 0
            user_limits.voice_messages_used = 0
            user_limits.reset_date = datetime.datetime.utcnow()
            
            session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def get_all_users(session=None):
        """Get all users"""
        try:
            users = session.query(User).all()
            return users
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def get_active_users(days=7, session=None):
        """Get users active in the last X days"""
        try:
            cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            active_users = session.query(User).filter(User.last_activity >= cutoff_date).all()
            return active_users
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def get_user_referral_code(user_id, session=None):
        """Get the referral code for a user"""
        try:
            user = session.query(User).get(user_id)
            if not user:
                return None
            
            return user.referral_code
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def get_user_info_by_telegram_id(telegram_id, session=None):
        """Get user information by telegram ID without returning detached objects"""
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            
            if not user:
                return None
            
            # Extract all needed information
            user_info = {
                'id': user.id,
                'telegram_id': user.telegram_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'referral_code': user.referral_code,
                'created_at': user.created_at,
                'last_activity': user.last_activity
            }
            
            return user_info
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    @with_session
    async def reset_daily_free_messages(session=None):
        """Reset daily free messages for all users"""
        try:
            # Get all users with limits
            users_with_limits = session.query(UserLimit).all()
            
            # Get daily free message setting from admin settings
            from bot.services.admin_service import AdminService
            daily_free_messages = int(await AdminService.get_setting('DAILY_FREE_MESSAGES', DAILY_FREE_MESSAGES))
            
            for user_limit in users_with_limits:
                # Check if user has active subscription
                from bot.services.subscription_service import SubscriptionService
                active_subs = await SubscriptionService.get_user_active_subscriptions(user_limit.user_id)
                
                # Only add free messages if user doesn't have active subscription
                if not active_subs:
                    user_limit.text_messages_limit += daily_free_messages
                    
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error resetting daily free messages: {str(e)}")
