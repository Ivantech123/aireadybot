from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/bot.db')

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionFactory = sessionmaker(bind=engine)

# Create scoped session for thread safety
Session = scoped_session(SessionFactory)

# Base class for all models
Base = declarative_base()

async def init_db():
    """Initialize the database, creating all tables"""
    from database.models import Base, User, UserLimit, Transaction, MessageLog, StarPackage, AdminSettings, Advertisement, BroadcastMessage, SubscriptionPlan, Subscription
    from bot.services.subscription_service import SubscriptionService
    Base.metadata.create_all(engine)
    
    # Initialize default settings if they don't exist
    session = Session()
    try:
        # Check if we have default star packages
        star_packages = session.query(StarPackage).all()
        if not star_packages:
            default_packages = [
                StarPackage(name="Small Pack", stars_amount=50, price=5.0),
                StarPackage(name="Medium Pack", stars_amount=150, price=10.0),
                StarPackage(name="Large Pack", stars_amount=500, price=20.0)
            ]
            session.add_all(default_packages)
        
        # Check if we have default admin settings
        settings = session.query(AdminSettings).all()
        if not settings:
            default_settings = [
                AdminSettings(setting_name="free_text_messages_limit", setting_value=os.getenv('FREE_TEXT_MESSAGES_LIMIT', '5')),
                AdminSettings(setting_name="free_image_generation_limit", setting_value=os.getenv('FREE_IMAGE_GENERATION_LIMIT', '1')),
                AdminSettings(setting_name="referral_reward_stars", setting_value=os.getenv('REFERRAL_REWARD_STARS', '10')),
                AdminSettings(setting_name="text_message_stars_cost", setting_value="2"),
                AdminSettings(setting_name="image_generation_stars_cost", setting_value="5"),
                AdminSettings(setting_name="voice_message_stars_cost", setting_value="3")
            ]
            session.add_all(default_settings)
        
        # Default advertisement text
        ads = session.query(Advertisement).all()
        if not ads:
            default_ad = Advertisement(text="Try our premium features! Use /subscribe to get more stars.")
            session.add(default_ad)
            
        session.commit()
        
        # Initialize subscription plans
        await SubscriptionService.initialize_subscription_plans()
        
    except Exception as e:
        session.rollback()
        print(f"Error initializing database: {e}")
    finally:
        session.close()

def get_session():
    """Get a database session"""
    return Session()
