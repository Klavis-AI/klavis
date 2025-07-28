from .base import (
    auth_token_context
)

from .schedule import (
    cal_get_all_schedules,
    cal_create_a_schedule,
    cal_update_a_schedule,
    cal_get_default_schedule,
    cal_get_schedule,
    cal_delete_a_schedule
)

from .stripe import (
    cal_get_stripe_connect_url,
    cal_save_stripe_credentials,
    cal_check_stripe_connection
)

from .verified_resources import (
    cal_request_email_verification_code,
    cal_verify_email_code,
    cal_get_verified_emails,
    cal_get_verified_email_by_id,

    # Not added functions that were not working on my side, but in the code -
    # cal_request_phone_verification_code,
    # cal_verify_phone_code,

    cal_get_verified_phones,
    cal_get_verified_phone_by_id
)

from .webhooks import (
    cal_get_all_webhooks,
    cal_create_webhook,
    cal_get_webhook,
    cal_update_webhook,
    cal_delete_webhook
)

__all__ = [
    # base.py
    "auth_token_context",

    # schedule.py
    "cal_get_all_schedules",
    "cal_create_a_schedule",
    "cal_update_a_schedule",
    "cal_get_default_schedule",
    "cal_get_schedule",
    "cal_delete_a_schedule",

    # stripe.py
    "cal_get_stripe_connect_url",
    "cal_save_stripe_credentials",
    "cal_check_stripe_connection",

    # verified_resources.py
    "cal_request_email_verification_code",
    "cal_verify_email_code",
    "cal_get_verified_emails",
    "cal_get_verified_email_by_id",

    # Not added functions that were not working on my side, but in the code -
    # 'cal_request_phone_verification_code',
    # 'cal_verify_phone_code',

    "cal_get_verified_phones",
    "cal_get_verified_phone_by_id",

    # webhooks.py
    "cal_get_all_webhooks",
    "cal_create_webhook",
    "cal_get_webhook",
    "cal_update_webhook",
    "cal_delete_webhook"
]