from database.db import get_session
from database.models import User, Transaction, StarPackage
from sqlalchemy import func
import datetime
from config.config import TEXT_MESSAGE_STARS_COST, IMAGE_GENERATION_STARS_COST, VOICE_MESSAGE_STARS_COST

class PaymentService:
    @staticmethod
    async def get_star_packages():
        """Get all available star packages"""
        session = get_session()
        try:
            packages = session.query(StarPackage).filter(StarPackage.is_active == True).all()
            return packages
        finally:
            session.close()
    
    @staticmethod
    async def purchase_stars(user_id, package_id):
        """Process a star package purchase"""
        session = get_session()
        try:
            package = session.query(StarPackage).filter(
                StarPackage.id == package_id,
                StarPackage.is_active == True
            ).first()
            
            if not package:
                return False, "Package not found or inactive"
            
            user = session.query(User).get(user_id)
            if not user:
                return False, "User not found"
            
            # Add stars to user's account
            user.stars += package.stars_amount
            
            # Record transaction
            transaction = Transaction(
                user_id=user_id,
                amount=package.stars_amount,
                description=f"Purchased {package.stars_amount} stars ({package.name})",
                transaction_type="purchase"
            )
            
            session.add(transaction)
            session.commit()
            
            return True, f"Successfully purchased {package.stars_amount} stars"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    async def check_stars_for_service(user_id, service_type):
        """Check if user has enough stars for a service"""
        session = get_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return False, 0, 0
            
            # Get cost based on service type
            if service_type == 'text':
                cost = TEXT_MESSAGE_STARS_COST
            elif service_type == 'image':
                cost = IMAGE_GENERATION_STARS_COST
            elif service_type == 'voice':
                cost = VOICE_MESSAGE_STARS_COST
            else:
                return False, 0, 0
            
            has_enough = user.stars >= cost
            return has_enough, user.stars, cost
        finally:
            session.close()
    
    @staticmethod
    async def use_stars_for_service(user_id, service_type):
        """Use stars for a service"""
        session = get_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return False, "User not found"
            
            # Get cost based on service type
            if service_type == 'text':
                cost = TEXT_MESSAGE_STARS_COST
                description = "Used stars for text message"
            elif service_type == 'image':
                cost = IMAGE_GENERATION_STARS_COST
                description = "Used stars for image generation"
            elif service_type == 'voice':
                cost = VOICE_MESSAGE_STARS_COST
                description = "Used stars for voice message"
            else:
                return False, "Invalid service type"
            
            # Check if user has enough stars
            if user.stars < cost:
                return False, "Not enough stars"
            
            # Deduct stars
            user.stars -= cost
            
            # Record transaction
            transaction = Transaction(
                user_id=user_id,
                amount=-cost,
                description=description,
                transaction_type="usage"
            )
            
            session.add(transaction)
            session.commit()
            
            return True, f"Successfully used {cost} stars"
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    async def get_user_transactions(user_id, limit=10):
        """Get recent transactions for a user"""
        session = get_session()
        try:
            transactions = session.query(Transaction).filter(
                Transaction.user_id == user_id
            ).order_by(Transaction.transaction_date.desc()).limit(limit).all()
            
            return transactions
        finally:
            session.close()
