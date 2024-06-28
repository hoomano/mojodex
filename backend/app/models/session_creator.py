from mojodex_core.db import with_db_session
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdUser, MdSession
from datetime import datetime
import hashlib
import random
import string

class SessionCreator:
    @staticmethod
    def generate_session_id(user_id):
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        clear_string = f"{random_string}_mojodex_{user_id}_{datetime.now().isoformat()}"
        encoded_string = hashlib.md5(clear_string.encode())
        return encoded_string.hexdigest()

    @with_db_session
    def create_session(self, user_id, platform, starting_mode, db_session):
        try:

            user = db_session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if user is None:
                log_error(f"Error creating session : User with user_id {user_id} does not exist")
                return {"error": f"Invalid user user_id: {user_id}"}, 400

            # check if user has agreed to terms and conditions
            if user.terms_and_conditions_accepted is None:
                log_error(
                    f"Error creating session : User with user_id {user_id} has not agreed to terms and conditions")
                return {"error": f"Terms and conditions not accepted"}, 401

            session_id = SessionCreator.generate_session_id(user_id)

            session = MdSession(session_id=session_id, user_id=user.user_id,
                                creation_date=datetime.now(), platform=platform, starting_mode=starting_mode, language=user.language_code)
            db_session.add(session)
            db_session.commit()

            return {"session_id": session_id, "intro_done": user.company_fk is not None}, 200

        except Exception as e:
            log_error(f"Error creating session : {e}")
            return {"error": f"Error creating session: {e}"}, 500