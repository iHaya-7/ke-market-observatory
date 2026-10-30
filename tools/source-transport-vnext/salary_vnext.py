"""Field-scoped salary observations using existing money grammar and salary rules.

Observed amounts survive missing dimensions. Geography never supplies currency,
period or pay applicability. Machine source verification is not human approval.
"""
import math
import base64
import re
import sys
from datetime import date

import consumer_vnext as consumer
import transport_vnext as t
sys.path.insert(0, str(t.ROOT / 'scripts'))
from refresh import salary_info

ANNUAL = re.compile(r'\b(?:annual (?:base (?:salary|pay)|salary|pay|compensation)|annually|per year|a year|yearly)\b', re.I)
MONTHLY = re.compile(r'\b(?:monthly (?:base (?:salary|pay)|salary|pay|compensation)|per month|a month)\b', re.I)
NON_PAY = re.compile(r'\b(?:funding|fundraising|revenue|raised|salary expectations?|desired salary)\b', re.I)
SIGNAL = re.compile(r'(?:\$|£|€|\bUSD|\bGBP|\bEUR|\bSAR|\bCAD|\bAUD)\s*\d', re.I)


def explicit_market(text):
    match = re.search(r'\b(US|United States|Saudi Arabia|United Kingdom|UK)(?:\s*[-–—]\s*Remote)?\s+(?:base salary|pay range)\b', text, re.I)
    return {'us': 'United States', 'united states': 'United States', 'saudi arabia': 'Saudi Arabia',
            'united kingdom': 'United Kingdom', 'uk': 'United Kingdom'}.get(match[1].casefold()) if match else None


def assess(packet, consumed, market, fx):
    record, kind = packet['record'], packet['source']['type']
    observations, signals, unhandled = [], [], []
    supported = {'pay_input_ranges'} if kind == 'greenhouse' else {'salaryRange', 'salaryDescription', 'salaryDescriptionPlain'} if kind == 'lever' else set()
    for area, values in [('record', record)] + [('originalRecord', t.loads(base64.b64decode(packet['captures'][0]['bytes_base64'])).get('originalRecord', {}))]:
        for key, value in values.items():
            if (not re.search(r'salary|compensation|^pay_', key, re.I) or value in (None, '', [], {})
                    or key in supported or area == 'originalRecord' and key in record):
                continue
            unhandled.append(dict(source=t.reference(packet, '/' + t.escape(key)) if area == 'record' else
                                  {'capture_sha256': packet['primary_capture_sha256'], 'pointer': '/originalRecord/' + t.escape(key)},
                                  value=value, reason='Structured pay field preserved; provider shape is not mapped'))

    def add(lo, hi, currency, period, label, locators, raw, pay_market=None):
        currency = currency.upper() if isinstance(currency, str) else None
        interval = {'Annual': 'per-year', 'Monthly': 'per-month'}.get(period)
        # Adapt only dimensions explicitly present in this observation. Existing
        # salary_info supplies compensation-basis and intrinsic eligibility rules.
        assessment = salary_info({'salaryRange': dict(min=lo, max=hi, currency=currency, interval=interval),
                                  'salaryDescriptionPlain': label}, 'lever', '')
        # The existing assessor returns early when units are missing. Preserve
        # independently explicit basis using its identical base/total predicates.
        total = bool(re.search(r'\b(total compensation|total remuneration|on[- ]target earnings|OTE|base (?:salary|pay) (?:and|\+) (?:bonus|equity))\b', label, re.I))
        base = bool(re.search(r'\b(base (?:salary|pay|compensation)|salary base|basic salary)\b', label, re.I))
        basis = 'unknown' if total and base else 'total' if total else 'base' if base else 'unknown'
        missing = [key for key, value in [('currency', currency), ('period', period),
                   ('compensation_basis', basis if basis != 'unknown' else None),
                   ('pay_market', pay_market)] if not value]
        numeric = type(lo) in (int, float) and math.isfinite(lo) and lo >= 0 and (hi is None or
                  type(hi) in (int, float) and math.isfinite(hi) and hi >= lo)
        rate = fx.get('rates', {}).get(currency)
        valid_fx = type(rate) in (int, float) and math.isfinite(rate) and rate > 0
        try: date.fromisoformat(fx.get('date', ''))
        except (TypeError, ValueError): valid_fx = False
        comparable = bool(numeric and not missing and assessment['salaryEligible'] and valid_fx
                          and market.get('decision') == 'Accept'
                          and pay_market == market.get('location', {}).get('country'))
        obs = dict(original=raw, lower_amount=lo, upper_amount=hi, currency=currency, period=period,
                   compensation_basis=basis, pay_market=pay_market,
                   intrinsic_eligible=bool(assessment['salaryEligible']), comparable=comparable,
                   unresolved_dimensions=missing, evidence=locators, normalized=None,
                   status='Source-verified comparable base pay' if comparable else 'Not comparable',
                   reason='All required dimensions resolve to source evidence.' if comparable else '; '.join(
                       ([('Unresolved: ' + ', '.join(missing))] if missing else [])
                       + (['Invalid numeric range'] if not numeric else [])
                       + (['Not base compensation'] if basis == 'total' else [])
                       + (['Posting is excluded or unresolved under market rules'] if market.get('decision') != 'Accept' else [])
                       + (['Pay applicability differs from posting geography'] if pay_market and pay_market != market.get('location', {}).get('country') else [])
                       + (['Supported FX rate/date unavailable'] if not valid_fx else [])
                       + (['Supported salary units required'] if period not in ('Annual', 'Monthly') else [])))
        if comparable:
            factor = rate / (12 if period == 'Annual' else 1)
            obs['normalized'] = dict(currency='SAR', period='Monthly', lower_amount=lo * factor,
                                     upper_amount=hi * factor if hi is not None else None,
                                     rate=rate, fx_date=fx['date'], fx_reference=fx)
        observations.append(obs)

    if kind == 'lever' and isinstance(record.get('salaryRange'), dict):
        raw = record['salaryRange']
        period = consumer.PERIODS.get(raw.get('interval')) or {'annual': 'Annual', 'per-year': 'Annual', 'monthly': 'Monthly', 'per-month': 'Monthly'}.get(raw.get('interval'))
        label = record.get('salaryDescriptionPlain') or record.get('salaryDescription') or ''
        refs = [dict(source=t.reference(packet, '/salaryRange'), transform='json')]
        for key in ('salaryDescriptionPlain', 'salaryDescription'):
            if record.get(key): refs.append(dict(source=t.reference(packet, '/' + key), transform='json'))
        add(raw.get('min'), raw.get('max'), raw.get('currency'), period, label, refs, raw, explicit_market(label))
    if kind == 'greenhouse':
        for index, raw in enumerate(record.get('pay_input_ranges') or []):
            label = str(raw.get('title', '')) + ' ' + str(raw.get('blurb', ''))
            period = 'Annual' if ANNUAL.search(label) and not MONTHLY.search(label) else 'Monthly' if MONTHLY.search(label) and not ANNUAL.search(label) else None
            lo = raw.get('min_cents'); hi = raw.get('max_cents')
            add(lo / 100 if type(lo) in (int, float) else None, hi / 100 if type(hi) in (int, float) else None,
                raw.get('currency_type'), period, label,
                [dict(source=t.reference(packet, '/pay_input_ranges/' + str(index)), transform='json')], raw, explicit_market(label))
    seen = set()
    for doc in consumed.get('documents', []):
        if doc['alternative_to']: continue
        rows = list(re.finditer(r'[^\n]+', doc['text']))
        for i, row in enumerate(rows):
            line = row.group()
            if NON_PAY.search(line): continue
            heading = rows[i-1].group() if i else ''
            if len(heading) >= 100 or consumer.primitives.MONEY.search(heading) or not re.search(r'\b(?:salary|base pay|compensation|pay range)\b', heading, re.I): heading = ''
            band = (heading + '\n' if heading else '') + line
            start = rows[i-1].start() if heading else row.start()
            locator = dict(source=doc['source'], transform=doc['transform'], start=start, end=row.end())
            t.require(consumer.resolve_evidence(packet, locator) == band, 'Salary passage fails source resolution')
            matches = list(consumer.primitives.MONEY.finditer(line))
            if SIGNAL.search(line) and not matches:
                signals.append(dict(text=line, locator=locator, reason='Unsupported numeric salary format; no amount inferred'))
            for match in matches:
                if not re.search(r'\b(?:salary|base pay|compensation|pay range|per year|a year|per month)\b', band, re.I):
                    signals.append(dict(text=line, locator=locator, reason='Amount is not explicitly established as offered salary'))
                    continue
                key = (band, match.start(), match.end())
                if key in seen: continue
                seen.add(key)
                codes = set(c.upper() for c in re.findall(r'\b(?:USD|GBP|EUR|SAR|CAD|AUD)\b', band, re.I))
                currency = next(iter(codes)) if len(codes) == 1 else {'£': 'GBP', '€': 'EUR'}.get(match['symbol']) if not codes else None
                annual, monthly = bool(ANNUAL.search(band)), bool(MONTHLY.search(band))
                period = 'Annual' if annual and not monthly else 'Monthly' if monthly and not annual else None
                pay_market = explicit_market(band)
                add(float(match['lo'].replace(',', '')), float(match['hi'].replace(',', '')), currency, period,
                    band, [dict(text=band, locator=locator)], dict(text=match.group()), pay_market)
    status = 'No salary disclosed in consumed fields' if not observations and not signals and not unhandled else (
        'Source-verified comparable base pay' if any(o['comparable'] for o in observations) else 'Salary evidence unresolved or excluded')
    result = dict(status=status, observations=observations, unparsed_signals=signals, unhandled_structured_fields=unhandled,
                comparable_observations=sum(o['comparable'] for o in observations), production_approval=None,
                salaryMin=None, salaryMax=None, currency=None, period=None, salaryEligible=False,
                salaryBasis='none', salaryBasisVerified=False, compensation=status, salaryReview=None,
                limitation='Only explicit source dimensions are used. No currency/period/pay-market inference from posting geography; no human approval inferred.')
    if len(observations) == 1 and observations[0]['comparable']:
        obs = observations[0]
        result.update(salaryMin=obs['lower_amount'], salaryMax=obs['upper_amount'], currency=obs['currency'],
                      period=obs['period'], salaryBasis='base', salaryBasisVerified=True, salaryEligible=True)
    return result
