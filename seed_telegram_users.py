import datetime
import random
from sqlalchemy.orm import Session
from backend_service.core.database import SessionLocal, init_db
from backend_service.core.models.session import Session as SessionModel
from backend_service.core.models.message import Message as MessageModel
from backend_service.core.models.action_log import AgentActionLog

def seed_data():
    db = SessionLocal()
    
    print("Clearing old mock sessions and messages...")
    db.query(AgentActionLog).delete()
    db.query(MessageModel).delete()
    db.query(SessionModel).delete()
    db.commit()

    print("Generating 30 Telegram Users (Sessions)...")
    
    base_time = datetime.datetime.now() - datetime.timedelta(days=7)
    
    # Pre-defined chat snippets for variety (based on company_info.json Syrian ADSL/IPTV)
    chat_snippets = [
        [
            ("user", "السلام عليكم"),
            ("bot", "وعليكم السلام، كيف يمكنني مساعدتك اليوم؟"),
            ("user", "النت قاطع عندي من الصبح"),
            ("bot", "عذراً لذلك، هل يمكنك تزويدي برقم الهاتف المسجل لدينا لنقوم بفحص الخط؟")
        ],
        [
            ("user", "مرحبا، ما هي عروضكم للـ ADSL؟"),
            ("bot", "أهلاً بك. لدينا عدة باقات ADSL شهرية، على سبيل المثال باقة 1 MB بحجم استهلاك 50 GB بسعر 185,000 ل.س، وباقة 2 MB بسعر 240,000 ل.س. هل تود معرفة سرعات أعلى؟"),
            ("user", "ما هي باقة الـ 4 ميغا؟"),
            ("bot", "باقة 4 MB توفر لك 140 GB استهلاك شهري بسعر 380,000 ل.س، وبعد انتهاء الباقة تصبح السرعة 512 KB.")
        ],
        [
            ("user", "اريد تجديد اشتراكي"),
            ("bot", "أهلاً بك، يرجى تزويدي برقم الهاتف المرتبط بالاشتراك للتحقق من الرصيد والباقة الحالية."),
            ("user", "0993311844"),
            ("bot", "تم التحقق، باقتك الحالية هي 8 MB. التكلفة 640,000 ل.س. هل تريدني أن أقوم بالتجديد الآن؟")
        ],
        [
            ("user", "شو هي باقات الـ IPTV عندكم؟"),
            ("bot", "لدينا باقات IPTV متنوعة. على سبيل المثال باقة PRO (SPORT) بسعر 175,000 ل.س، وباقة PRO (FAMILY) بسعر 220,000 ل.س. هل أنت مهتم بالباقات الرياضية أم العائلية؟"),
            ("user", "بدي الرياضية"),
            ("bot", "ممتاز. باقة الرياضة تكلف 175,000 ل.س. ملاحظة: هناك رسوم اشتراك للمرة الأولى بقيمة 52,000 ل.س.")
        ],
        [
            ("user", "انتهت الباقة عندي، كيف بقدر زيد الرصيد؟"),
            ("bot", "يمكنك شراء بطاقات التعبئة الإضافية (Top-up). مثلاً 10 GB بسعر 33,000 ل.س أو 20 GB بسعر 57,000 ل.س. أي حجم ترغب بإضافته؟"),
            ("user", "10 غيغا بكفي"),
            ("bot", "يرجى تأكيد رقم الخط الخاص بك لنتمكن من إضافة الـ 10 GB (33,000 ل.س).")
        ],
        [
            ("user", "ممكن رقم الدعم الفني؟"),
            ("bot", "بالتأكيد. يمكنك التواصل مع الدعم الفني على الرقم 0932274222.")
        ]
    ]

    for i in range(1, 31):
        # Determine authentication state randomly (approx 60% authenticated)
        is_authed = random.random() > 0.4
        auth_state = "AUTHENTICATED" if is_authed else "UNAUTHENTICATED"
        customer_id = f"C{i:03d}" if is_authed else None
        
        session_id = f"tg_user_{random.randint(10000, 99999)}_{i}"
        
        # Session creation time varies from 7 days ago to now
        created_at = base_time + datetime.timedelta(hours=random.randint(0, 168))
        
        s = SessionModel(
            session_id=session_id,
            user_id=session_id,
            customer_id=customer_id,
            is_active=random.choice([True, True, False]), # 2/3 active
            authed=is_authed,
            auth_state=auth_state,
            created_at=created_at
        )
        db.add(s)
        
        # Generate messages for this session
        messages = random.choice(chat_snippets)
        msg_time = created_at
        for j, (sender, content) in enumerate(messages):
            msg_time = msg_time + datetime.timedelta(minutes=random.randint(1, 10))
            msg = MessageModel(
                session_id=session_id,
                sender=sender,
                content=content,
                created_at=msg_time
            )
            db.add(msg)
            
    db.commit()
    db.close()
    print("Database seeding of 30 users completed successfully.")

if __name__ == "__main__":
    init_db()
    seed_data()
