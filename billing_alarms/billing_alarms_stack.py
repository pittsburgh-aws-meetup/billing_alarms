from aws_cdk import core, aws_budgets, aws_sns as sns, aws_sns_subscriptions as sns_sub
from jsii.errors import JSIIError
from yaml import safe_load
import os


class BillingAlarmsStack(core.Stack):
    VALID_NOTIFICATIONS = ['sms', 'email', 'both']
    VALID_CURRENCY = ['USD']

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        with open('config.yml') as file:
            config = safe_load(file)
        phone = self._get_phone_number(config)
        email = self._get_email(config)
        self._check_if_setup(email, phone)
        value = self._get_budget_amount(config)
        currency = self._get_currency(config)
        nws = []
        topics = {}
        subs = {}
        for notification in config['notifications']:
            mechanism = notification['mechanism']
            threshold = notification['threshold']
            if mechanism not in topics.keys():
                low_mech = mechanism.lower()
                topics[mechanism] = sns.Topic(self, id=f"{low_mech}_notification_topic",
                                              display_name=f"{low_mech} budget notifications",
                                              topic_name=f"{low_mech}_budget_notification")
            if mechanism not in subs.keys():
                subs[mechanism] = self._build_sub(mechanism, phone, email)
            relevant_topic = topics[mechanism]
            relevant_sub = subs[mechanism]
            try:
                relevant_topic.add_subscription(relevant_sub)
            except JSIIError:
                # This exception is thrown when the subscription has already been added to the topic.
                # Hence we pass, as the task is already done.
                pass
            nws.append(self._build_notwsub(relevant_topic, threshold))

        budget_data_props = aws_budgets.CfnBudget.BudgetDataProperty(budget_type='COST', time_unit='MONTHLY',
                                                                     budget_name='CDK budget',
                                                                     budget_limit=aws_budgets.CfnBudget.SpendProperty(
                                                                         amount=value, unit=currency))
        aws_budgets.CfnBudget(self, 'cdk budget', budget=budget_data_props, notifications_with_subscribers=nws)

    @staticmethod
    def _build_notwsub(topic, threshold):
        np = aws_budgets.CfnBudget.NotificationProperty(comparison_operator='GREATER_THAN',
                                                        notification_type='FORECASTED', threshold=threshold,
                                                        threshold_type='PERCENTAGE')
        sub_prop = aws_budgets.CfnBudget.SubscriberProperty(address=topic.topic_arn, subscription_type='SNS')
        return aws_budgets.CfnBudget.NotificationWithSubscribersProperty(notification=np, subscribers=[sub_prop])

    @classmethod
    def _build_sub(cls, mechanism, phone, email):
        if mechanism == 'email':
            return sns_sub.EmailSubscription(email)
        elif mechanism == 'sms':
            return sns_sub.SmsSubscription(phone)
        else:
            raise ValueError(
                f"Notification mechanism '{mechanism}', must be one of {', '.join(cls.VALID_NOTIFICATIONS)}")

    @staticmethod
    def _check_if_setup(email, phone):
        if email == '<email_address>' or phone == '<phone_number>':
            raise RuntimeError('Please edit the config.yml to your specifications.  See the README for guidance.')

    @staticmethod
    def _get_budget_amount(config) -> float:
        amount = os.getenv('amount')
        if amount is None:
            amount = config['budget']['amount']
        return float(amount)

    @classmethod
    def _get_currency(cls, config) -> str:
        currency = os.getenv('currency')
        if currency is None:
            currency = config['budget']['currency']
        if currency not in cls.VALID_CURRENCY:
            raise ValueError(f"Currency '{currency}' is invalid, must be one of {', '.join(cls.VALID_CURRENCY)}")
        return str(currency)

    @staticmethod
    def _get_email(config) -> str:
        email = os.getenv('email')
        if email is None:
            email = config['email']
        return str(email)

    @staticmethod
    def _get_phone_number(config) -> str:
        phone = os.getenv('phone')
        if phone is None:
            phone = config['phone']
        return str(phone)
