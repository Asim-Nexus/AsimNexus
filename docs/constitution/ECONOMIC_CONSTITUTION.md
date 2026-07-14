# Economic Constitution

> **Tokenomics, staking, marketplace rules, and escrow for Digital Nepal**

## Overview

The AsimNexus Economic Constitution defines the rules governing digital economic activities within the Digital Nepal ecosystem. It covers tokenomics, staking, marketplace operations, escrow services, and financial compliance.

## Article I: Digital Currency

### Section 1: Native Token

The AsimNexus ecosystem uses a native utility token for:

1. **Transaction Fees** — Pay for system operations
2. **Staking** — Secure network participation
3. **Governance** — Vote on proposals
4. **Incentives** — Reward contributions
5. **Value Exchange** — Trade goods and services

### Section 2: Token Economics

| Parameter | Value | Notes |
|-----------|-------|-------|
| Total Supply | 1,000,000,000 | Fixed supply, no inflation |
| Circulating | 500,000,000 | Gradually released |
| Staked | 300,000,000 | Locked in staking contracts |
| Treasury | 100,000,000 | Reserved for ecosystem growth |
| Team | 100,000,000 | 4-year vesting schedule |

### Section 3: Transaction Fees

1. **Standard Transactions** — 0.1% fee
2. **Government Transactions** — 0.05% fee (subsidized)
3. **Enterprise Transactions** — 0.2% fee
4. **Citizen Transactions** — 0.1% fee
5. **Emergency Transactions** — 0% fee (during emergencies)

## Article II: Staking

### Section 1: Staking Pools

| Pool | Min Stake | Duration | APY | Purpose |
|------|:---------:|:--------:|:---:|---------|
| Security | 1,000 | 30 days | 5% | Network security |
| Governance | 100 | 7 days | 3% | Voting rights |
| Liquidity | 10,000 | 14 days | 8% | Market liquidity |
| Infrastructure | 5,000 | 90 days | 12% | Node operation |

### Section 2: Rewards

1. Rewards are distributed daily
2. Rewards are proportional to stake amount and duration
3. Early unstaking incurs a penalty (10% of rewards)
4. Rewards are automatically compounded

### Section 3: Slashing

Stakes can be slashed for:

1. **Malicious Behavior** — 100% of stake
2. **Protocol Violation** — 50% of stake
3. **Inactivity** — 10% of stake
4. **False Reporting** — 25% of stake

## Article III: Marketplace

### Section 1: Listing Rules

1. All listings must comply with Nepal's digital commerce laws
2. Prohibited items cannot be listed (weapons, drugs, etc.)
3. Listings must include accurate descriptions
4. Pricing must be in native tokens or NPR equivalent

### Section 2: Transaction Rules

1. All marketplace transactions use smart escrow
2. Funds are held in escrow until delivery is confirmed
3. Disputes are resolved through the Dharma Veto Engine
4. Marketplace fees are 2% per transaction

### Section 3: Ratings and Reputation

1. Buyers and sellers rate each other after transactions
2. Ratings are on a 1-5 scale
3. Reputation is non-transferable
4. Low-rated participants face transaction limits

## Article IV: Escrow

### Section 1: Smart Escrow

All financial transactions use smart escrow:

1. **Deposit** — Buyer deposits funds into escrow
2. **Delivery** — Seller delivers goods/services
3. **Confirmation** — Buyer confirms receipt
4. **Release** — Funds are released to seller
5. **Dispute** — If no confirmation, dispute resolution begins

### Section 2: Escrow Periods

| Transaction Type | Escrow Period | Auto-Release |
|-----------------|:-------------:|:------------:|
| Digital Goods | 24 hours | After 24h no dispute |
| Physical Goods | 7 days | After 7d no dispute |
| Services | 14 days | After 14d no dispute |
| Government Services | 48 hours | After 48h no dispute |

### Section 3: Dispute Resolution

1. **Mediation** — Automated mediation (24 hours)
2. **Arbitration** — Human arbitrator review (48 hours)
3. **Dharma Review** — Dharma Engine binding decision (24 hours)
4. **Appeal** — Constitutional Council (7 days)

## Article V: Enterprise Economics

### Section 1: Licensing Fees

| License Tier | Annual Fee | Features |
|-------------|:----------:|----------|
| FREE | 0 | Basic access, 1 agent |
| STARTER | 1,000 | 5 agents, basic analytics |
| BUSINESS | 10,000 | 25 agents, advanced analytics |
| ENTERPRISE | 100,000 | Unlimited agents, full features |
| GOVERNMENT | 0 | Special government license |

### Section 2: Revenue Sharing

1. **Platform Fee** — 2% of enterprise revenue
2. **Government Share** — 0.5% to government treasury
3. **Citizen Dividend** — 0.5% distributed to staking citizens
4. **Development Fund** — 1% to ecosystem development

## Article VI: Citizen Economics

### Section 1: Universal Basic Digital Income

1. Every verified citizen receives a basic digital income
2. Amount is determined by treasury and governance vote
3. Distributed monthly in native tokens
4. Can be staked for additional returns

### Section 2: Contribution Rewards

Citizens earn rewards for:

1. **Content Creation** — Per engagement metrics
2. **Data Contribution** — For sharing anonymized data
3. **Community Moderation** — For maintaining quality
4. **Bug Reporting** — For security vulnerability reports
5. **Translation** — For localization contributions

## Article VII: Compliance and Auditing

### Section 1: Financial Compliance

1. All transactions are recorded in the audit log
2. Large transactions (>100,000 tokens) require enhanced verification
3. Suspicious activity is reported to the compliance system
4. Annual financial audits are published

### Section 2: Tax Compliance

1. Platform automatically calculates applicable taxes
2. Tax filings are submitted to Nepal's tax authority
3. Citizens can view their tax history at any time
4. Tax payments are made in native tokens or NPR

## Implementation

The economic system is implemented across multiple modules:

- [`core/economy/`](../core/economy/) — Token, staking, escrow, marketplace
- [`routes/marketplace.py`](../routes/marketplace.py) — Marketplace API
- [`core/governance/enterprise_layer.py`](../core/governance/enterprise_layer.py) — Enterprise licensing
- [`tests/integration/test_economy_*.py`](../tests/integration/) — Economic test suites
