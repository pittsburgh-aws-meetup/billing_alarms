#!/usr/bin/env python3

from aws_cdk import core

from billing_alarms.billing_alarms_stack import BillingAlarmsStack


app = core.App()
BillingAlarmsStack(app, "billing-alarms")

app.synth()
