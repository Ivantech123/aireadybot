import datetime
from sqlalchemy import func
from database.db import get_session
from database.models import AdminSettings, Advertisement, BroadcastMessage, User, Transaction, StarPackage

class AdminService:
    @staticmethod
    async def get_advertisement():
        """Get the active advertisement text"""
        session = get_session()
        try:
            ad = session.query(Advertisement).filter(Advertisement.is_active == True).order_by(Advertisement.updated_at.desc()).first()
            return ad.text if ad else ""
        finally:
            session.close()
    
    @staticmethod
    async def set_advertisement(text, is_active=True):
        """Set a new advertisement text"""
        session = get_session()
        try:
            # Deactivate all current ads
            if is_active:
                session.query(Advertisement).update({Advertisement.is_active: False})
            
            # Create new ad
            ad = Advertisement(text=text, is_active=is_active)
            session.add(ad)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    async def verify_admin_password(password):
        """Verify admin password"""
        from config.config import ADMIN_PASSWORD
        return password == ADMIN_PASSWORD
    
    @staticmethod
    async def create_broadcast(text):
        """Create a new broadcast message"""
        session = get_session()
        try:
            # Count total users
            total_users = session.query(func.count(User.id)).filter(
                User.is_active == True,
                User.is_blocked == False
            ).scalar()
            
            # Create broadcast message
            broadcast = BroadcastMessage(
                text=text,
                total_count=total_users,
                status='pending'
            )
            
            session.add(broadcast)
            session.commit()
            return broadcast.id
        except Exception as e:
            session.rollback()
            return None
        finally:
            session.close()
    
    @staticmethod
    async def update_broadcast_status(broadcast_id, sent_count, status=None):
        """Update the status of a broadcast message"""
        session = get_session()
        try:
            broadcast = session.query(BroadcastMessage).get(broadcast_id)
            
            if not broadcast:
                return False
            
            broadcast.sent_count = sent_count
            
            if status:
                broadcast.status = status
                
                if status == 'completed':
                    broadcast.completed_at = datetime.datetime.utcnow()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    async def get_pending_broadcasts():
        """Get all pending broadcast messages"""
        session = get_session()
        try:
            broadcasts = session.query(BroadcastMessage).filter(
                BroadcastMessage.status.in_(['pending', 'in_progress'])
            ).all()
            return broadcasts
        finally:
            session.close()
    
    @staticmethod
    async def get_broadcast(broadcast_id):
        """Get a broadcast message by ID"""
        session = get_session()
        try:
            return session.query(BroadcastMessage).get(broadcast_id)
        finally:
            session.close()
    
    @staticmethod
    async def get_users_for_broadcast(offset, limit):
        """Get a batch of users for broadcasting"""
        session = get_session()
        try:
            users = session.query(User).filter(
                User.is_active == True,
                User.is_blocked == False
            ).order_by(User.id).offset(offset).limit(limit).all()
            return users
        finally:
            session.close()
    
    @staticmethod
    async def get_admin_settings():
        """Get all admin settings"""
        session = get_session()
        try:
            settings = session.query(AdminSettings).all()
            return {setting.setting_name: setting.setting_value for setting in settings}
        finally:
            session.close()
    
    @staticmethod
    async def update_admin_setting(setting_name, setting_value):
        """Update an admin setting"""
        session = get_session()
        try:
            setting = session.query(AdminSettings).filter(AdminSettings.setting_name == setting_name).first()
            
            if setting:
                setting.setting_value = str(setting_value)
            else:
                setting = AdminSettings(setting_name=setting_name, setting_value=str(setting_value))
                session.add(setting)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    async def get_star_packages():
        """Get all star packages"""
        session = get_session()
        try:
            packages = session.query(StarPackage).filter(StarPackage.is_active == True).all()
            return packages
        finally:
            session.close()
    
    @staticmethod
    async def update_star_package(package_id, name, stars_amount, price, is_active=True):
        """Update a star package"""
        session = get_session()
        try:
            package = session.query(StarPackage).get(package_id)
            
            if not package:
                return False
            
            package.name = name
            package.stars_amount = stars_amount
            package.price = price
            package.is_active = is_active
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    async def create_star_package(name, stars_amount, price, is_active=True):
        """Create a new star package"""
        session = get_session()
        try:
            package = StarPackage(
                name=name,
                stars_amount=stars_amount,
                price=price,
                is_active=is_active
            )
            
            session.add(package)
            session.commit()
            return package.id
        except Exception as e:
            session.rollback()
            return None
        finally:
            session.close()
    
    @staticmethod
    async def get_transaction_stats():
        """Get transaction statistics"""
        session = get_session()
        try:
            # Total stars purchased
            total_purchased = session.query(func.sum(Transaction.amount)).filter(
                Transaction.transaction_type == 'purchase'
            ).scalar() or 0
            
            # Total stars used
            total_used = session.query(func.sum(Transaction.amount)).filter(
                Transaction.transaction_type == 'usage'
            ).scalar() or 0
            
            # Total referral rewards
            total_referral = session.query(func.sum(Transaction.amount)).filter(
                Transaction.transaction_type == 'referral_reward'
            ).scalar() or 0
            
            return {
                "total_purchased": total_purchased,
                "total_used": abs(total_used),
                "total_referral": total_referral
            }
        finally:
            session.close()
    
    @staticmethod
    async def search_users(query):
        """Search for users by ID, username, or name"""
        session = get_session()
        try:
            # Try to parse as telegram_id
            try:
                telegram_id = str(int(query))
                users_by_id = session.query(User).filter(User.telegram_id == telegram_id).all()
                if users_by_id:
                    return users_by_id
            except (ValueError, TypeError):
                pass
            
            # Search by username or name
            users = session.query(User).filter(
                (User.username.ilike(f"%{query}%")) |
                (User.first_name.ilike(f"%{query}%")) |
                (User.last_name.ilike(f"%{query}%"))
            ).limit(20).all()
            
            return users
        finally:
            session.close()

    @staticmethod
    async def update_advertisement(text):
        """Update the advertisement text"""
        return await AdminService.set_advertisement(text)
    
    @staticmethod
    async def send_broadcast(message_text):
        """Send a broadcast message to all users"""
        from bot.services.user_service import UserService
        
        try:
            # Create broadcast record
            broadcast_id = await AdminService.create_broadcast(message_text)
            
            if not broadcast_id:
                return False, 0
            
            # Get all active users
            users = await UserService.get_all_users()
            sent_count = 0
            
            # Update broadcast status to in_progress
            await AdminService.update_broadcast_status(broadcast_id, sent_count, 'in_progress')
            
            # Return success and count of users to send to
            # The actual sending will be handled by the bot
            return True, len(users)
        except Exception as e:
            print(f"Error sending broadcast: {e}")
            return False, 0
    
    @staticmethod
    async def get_user_stats():
        """Get user statistics"""
        from bot.services.user_service import UserService
        
        try:
            # Get all users
            all_users = await UserService.get_all_users()
            total_users = len(all_users)
            
            # Get active users in the last 7 days
            active_users = await UserService.get_active_users(days=7)
            active_users_count = len(active_users)
            
            # Get active users in the last 24 hours
            active_users_24h = await UserService.get_active_users(days=1)
            active_users_24h_count = len(active_users_24h)
            
            return {
                'total_users': total_users,
                'active_users_7d': active_users_count,
                'active_users_24h': active_users_24h_count
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return None

    @staticmethod
    async def get_setting(setting_name, default_value=None):
        """Get a setting value from admin settings"""
        session = get_session()
        try:
            setting = session.query(AdminSettings).filter(AdminSettings.setting_name == setting_name).first()
            return setting.setting_value if setting else default_value
        finally:
            session.close()
    
    @staticmethod
    async def set_setting(setting_name, setting_value):
        """Set a setting value in admin settings"""
        session = get_session()
        try:
            setting = session.query(AdminSettings).filter(AdminSettings.setting_name == setting_name).first()
            
            if setting:
                setting.setting_value = str(setting_value)
            else:
                setting = AdminSettings(setting_name=setting_name, setting_value=str(setting_value))
                session.add(setting)
                
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    async def get_free_message_settings():
        """Get all free message settings"""
        from config.config import FREE_TEXT_MESSAGES_LIMIT, FREE_IMAGE_GENERATION_LIMIT, DAILY_FREE_MESSAGES
        
        session = get_session()
        try:
            settings = {
                'initial_free_text': await AdminService.get_setting('FREE_TEXT_MESSAGES_LIMIT', FREE_TEXT_MESSAGES_LIMIT),
                'initial_free_images': await AdminService.get_setting('FREE_IMAGE_GENERATION_LIMIT', FREE_IMAGE_GENERATION_LIMIT),
                'daily_free_messages': await AdminService.get_setting('DAILY_FREE_MESSAGES', DAILY_FREE_MESSAGES)
            }
            return settings
        finally:
            session.close()
    
    @staticmethod
    async def update_free_message_settings(initial_free_text, initial_free_images, daily_free_messages):
        """Update free message settings"""
        try:
            await AdminService.set_setting('FREE_TEXT_MESSAGES_LIMIT', initial_free_text)
            await AdminService.set_setting('FREE_IMAGE_GENERATION_LIMIT', initial_free_images)
            await AdminService.set_setting('DAILY_FREE_MESSAGES', daily_free_messages)
            return True
        except Exception as e:
            return False
