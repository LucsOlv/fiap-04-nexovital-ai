@description('Nome do budget mensal.')
param budgetName string

@description('Email para notificações de orçamento.')
param notificationEmail string

resource budget 'Microsoft.Consumption/budgets@2024-08-01' = {
  name: budgetName
  properties: {
    amount: 5
    category: 'Cost'
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: '2026-07-01'
      endDate: '2030-12-31'
    }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: [
          notificationEmail
        ]
      }
      actual100: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        thresholdType: 'Actual'
        contactEmails: [
          notificationEmail
        ]
      }
    }
  }
}

output budgetNameOutput string = budget.name
