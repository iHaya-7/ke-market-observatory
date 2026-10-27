"""Offline HTML evidence adapter. No review labels, expectations, or corpus discovery.

html-blocks-v1: HTMLParser entity decoding, omit head/script/style/form, collapse
whitespace in each block, join blocks with LF. Offsets are Unicode code points.
Changing this transform requires a new version (locators depend on it).
"""
import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit, parse_qs

VERSION = 'captured-posting-v1'
TRANSFORM = 'html-blocks-v1'


def source_identity(url):
    parsed = urlsplit(url)
    host = {'boards.greenhouse.io': 'job-boards.greenhouse.io'}.get(parsed.hostname, parsed.hostname)
    job_id = parsed.path.rstrip('/').split('/')[-1]
    if parse_qs(parsed.query).get('gh_jid', [job_id]) != [job_id]:
        raise ValueError('Conflicting Greenhouse job identity')
    return host, parsed.path.rstrip('/')


class VisibleBlocks(HTMLParser):
    blocks = {'div', 'p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'section'}
    hidden = {'head', 'script', 'style', 'form', 'noscript'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = []
        self.parts, self.rows, self.metadata = [], [], {}

    def flush(self):
        value = ' '.join(''.join(self.parts).split())
        if value:
            self.rows.append(value)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('property', '').startswith('og:'):
            self.metadata[attrs['property']] = attrs.get('content', '')
        if tag in self.hidden:
            self.skip.append(tag)
        if not self.skip and tag in self.blocks:
            self.flush()

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
            return
        if tag in self.blocks:
            self.flush()

    def handle_data(self, value):
        if not self.skip:
            self.parts.append(value)


def visible(raw):
    parser = VisibleBlocks()
    parser.feed(raw.decode('utf-8'))
    parser.flush()
    return '\n'.join(parser.rows), parser.metadata


def resolve_html(raw, locator):
    if locator.get('transform') != TRANSFORM:
        raise ValueError('Unsupported HTML transform')
    text, _ = visible(raw)
    start, end = locator['start'], locator['end']
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
        raise ValueError('Invalid HTML span')
    return text[start:end]


DUTIES = re.compile(r"^(?:what you(?:['’]ll| will) (?:do|own).*|(?:key |areas of )?responsibilit(?:y|ies).*)$", re.I)
STOP = re.compile(r"^(?:what (?:we|you).*(?:looking|bring|required)|what excites.*|what.s required|who you are.*|requirements|.*qualifications|compensation|benefits|ai-augmented.*|what this role is not|what success looks like).*$", re.I)
ACTION = re.compile(r'^(?:(?:you (?:will|shall)|you[’\x27]ll)\s+)?(design|build|implement|maintain|create|define|model|develop|integrate|extend|validate|own|resolve|fuse|enforce|preserve|shape|contribute|support|write)\b', re.I)
DUTY_ACTION = re.compile(r'^(?:(?:you (?:will|shall)|you[’\x27]ll)\s+)?(?:design|build|implement|maintain|create|define|model|develop|integrate|extend|validate|own|resolve|fuse|enforce|preserve|shape|contribute|support|write|partner|help|turn|keep|make|detect|measure|use|instrument|protect|collaborate|improve|participate|champion|conduct|work|stay|proactively)\b', re.I)
REPRESENTATION = re.compile(r'\b(ontolog(?:y|ies)|knowledge graphs?|semantic model(?:ling|ing|s)?|RDF(?:/RDFS/OWL)?|SHACL|linked data|entity (?:resolution|linking)|knowledge representation)\b', re.I)


def interpret_duty(text):
    """Action/object evidence, confined to a duty clause; titles never enter here.

    General backend/query/ML work on a product named Knowledge Graph is adjacent.
    Qualifications, company prose and negated/speculative work cannot create links.
    """
    if not ACTION.search(text) or re.search(r'\b(?:not|never|no need to|may|might|maybe|familiarity|experience with)\b', text, re.I):
        return None
    clause = re.split(r'[.;]', text, maxsplit=1)[0]
    rep = REPRESENTATION.search(clause)
    if not rep:
        return None
    before_object = clause[ACTION.search(text).end():rep.start()]
    if re.search(r'\b(?:about|for|using|with|who|that|on|at|of)\b', before_object, re.I):
        return None
    # Require a representation task rather than any verb near a technology name.
    modeling = re.search(r'\b(?:design|build|maintain|implement|create|define|extend|validate|own|integrate|fuse|resolve|shape)\b', clause, re.I)
    platform = re.search(r'\b(?:backend features|API endpoints|query engine|operational maturity|integrations between|knowledge graph (?:service|API|backend))\b', clause, re.I)
    collateral = re.search(r'\b(?:presentations?|marketing|recruiting|sales|articles?|awareness|documentation|webpages|training materials)\b', clause, re.I)
    if not modeling or platform or collateral:
        return None
    return {'representation': rep.group(0), 'action': ACTION.search(text).group(1),
            'concept': 'ontology-engineer' if re.search(r'ontolog|SHACL|RDF', clause, re.I) else 'knowledge-graph-engineer',
            'rationale': 'Advertised duty explicitly acts on a knowledge representation: ' + clause}


# The grammar preserves bands independently. It never treats company funding,
# years, benefits or a salary-expectations question as an offered salary.
MONEY = re.compile(r'(?P<symbol>\$|£|€|USD\s*|GBP\s*|EUR\s*|SAR\s*|CAD\s*|AUD\s*)(?P<lo>\d[\d,]*(?:\.\d+)?)\s*(?:[-–—]|to)\s*(?:\$|£|€|USD\s*|GBP\s*|EUR\s*|SAR\s*|CAD\s*|AUD\s*)?(?P<hi>\d[\d,]*(?:\.\d+)?)', re.I)


def extract(raw, entry):
    text, metadata = visible(raw)
    if not text:
        raise ValueError('Empty captured source')
    if entry['job_title'] not in text:
        raise ValueError('Captured page does not contain its manifest job title')
    if metadata.get('og:url') and source_identity(metadata['og:url']) != source_identity(entry['requested_url']):
        raise ValueError('Captured source URL differs from manifest')
    passages = []

    def passage(start, end, kind):
        result = {'id': 'p' + str(len(passages)), 'text': text[start:end], 'kind': kind,
                  'locator': {'transform': TRANSFORM, 'start': start, 'end': end}}
        passages.append(result)
        return result

    full = passage(0, len(text), 'document context')
    rows = [(m.start(), m.end(), m.group()) for m in re.finditer(r'[^\n]+', text)]
    duties, sections, section_start, active, found, closed = [], [], None, False, False, False
    for start, end, line in rows:
        if DUTIES.fullmatch(line):
            active, found = True, True
            section_start = min(end + 1, len(text))
            continue
        if active and (STOP.fullmatch(line) or line.lower().startswith('apply for this job')):
            active, closed = False, True
            if section_start < start:
                sections.append(passage(section_start, start - 1, 'responsibility section')['id'])
        if active and DUTY_ACTION.search(line):
            p = passage(start, end, 'responsibility')
            duties.append({'passage': p['id'], 'text': line, 'mapping': interpret_duty(line)})
    # A delimited list supports a bounded negative; an unrecognized layout does not.
    coverage = 'delimited responsibility section' if found and closed and duties and not active else 'responsibilities unresolved'
    salaries = []
    previous_band_end = 0
    for index, (start, end, line) in enumerate(rows):
        for match in MONEY.finditer(line):
            if re.search(r'\b(?:funding|fundraising|revenue|raised|salary expectations?|desired salary)\b', line, re.I):
                continue
            nearby = rows[max(0, index-2):index+2]
            context = '\n'.join(r[2] for r in nearby)
            if not re.search(r'\b(?:salary|base pay|compensation|a year|per month)\b', context, re.I):
                continue
            # A separate immediately preceding base/period heading belongs to
            # this band, but distant annual leave/training never supplies units.
            heading = rows[index-1][2] if index and len(rows[index-1][2]) < 100 else ''
            if MONEY.search(heading) or not re.search(r'\b(?:salary|base pay|compensation)\b', heading, re.I):
                heading = ''
            band = heading + '\n' + line
            basis = 'base' if re.search(r'\b(?:base (?:salary|pay)|basic salary)\b', band, re.I) else None
            if re.search(r'\b(?:total compensation|on.target earnings|OTE)\b', band, re.I):
                basis = 'total' if not basis else 'ambiguous'
            period = 'Annual' if re.search(r'\b(?:annual (?:base (?:salary|pay)|salary|pay|total compensation)|annually|per year|a year|yearly)\b', band, re.I) else None
            if re.search(r'\b(?:monthly (?:base (?:salary|pay)|salary|pay)|per month|a month)\b|\bmonthly\s*[.]?$', band, re.I):
                period = 'Monthly' if not period else None
            codes = set(re.findall(r'\b(?:USD|GBP|EUR|SAR|CAD|AUD)\b', band, re.I))
            currency = next(iter(codes)).upper() if len(codes) == 1 else {'£': 'GBP', '€': 'EUR'}.get(match['symbol'])
            # "$" alone is ambiguous, even for a US posting. Retain this gap.
            p = passage(nearby[0][0], nearby[-1][1], 'salary context')
            # Explicit US salary applicability can occur in a preceding paragraph.
            context_start = max(previous_band_end, start-1800)
            before = text[context_start:end]
            market_match = re.search(r'(?:The (?:US|United States|Saudi Arabia|United Kingdom|UK) base salary range[^\n]*|The base salary range[^\n]*United States[^\n]*|United States Salary Range)', before, re.I)
            market = ('Saudi Arabia' if re.search('Saudi Arabia', market_match.group(), re.I) else
                      'United Kingdom' if re.search(r'United Kingdom|\bUK\b', market_match.group(), re.I) else 'United States') if market_match else None
            market_passage = passage(context_start + market_match.start(), context_start + market_match.end(), 'pay market') if market_match else None
            # Explicit role-scoped range on a single-location posting. This is a
            # contextual interpretation, retained verbatim rather than a country
            # inferred from employer headquarters, application forms or "$".
            location = metadata.get('og:description', '')
            if not market and location and ';' not in location and location in text and re.search(r'for this role\b', line, re.I):
                market = location
                loc_start = text.index(location)
                market_passage = passage(loc_start, loc_start + len(location), 'role location for role-scoped band')
            if market_match and not basis and re.search(r'base salary range', market_match.group(), re.I):
                basis = 'base'
            lo, hi = [float(match[x].replace(',', '')) for x in ('lo', 'hi')]
            salaries.append({'passage': p['id'], 'market_passage': market_passage['id'] if market_passage else None,
                             'lowerAmount': lo, 'upperAmount': hi, 'currency': currency, 'payPeriod': period,
                             'compensationBasis': basis, 'payMarket': market,
                             'bandApplicability': market_match.group() if market_match else None})
            previous_band_end = end
    return {'case_id': entry['candidate_id'], 'source_url': entry['requested_url'],
            'source_id': entry['requested_url'].split('/')[2] + '/' + entry['requested_url'].split('/')[3],
            'source_job_id': str(entry['upstream_job_id']), 'publisher': entry['employer'],
            'title': metadata.get('og:title', entry['job_title']), 'captured_at': entry['captured_utc'],
            'sha256': hashlib.sha256(raw).hexdigest(), 'member': entry['snapshot_file'],
            'passages': passages, 'context_passage': full['id'], 'responsibilities': duties,
            'responsibility_sections': sections,
            'responsibility_coverage': coverage, 'salaries': salaries,
            'identity_status': 'capture manifest attribution; not independently authenticated'}


def load_captures(archive):
    """Open only manifest-designated HTML members. Never extract or crawl a corpus."""
    archive = Path(archive)
    result = []
    with zipfile.ZipFile(archive) as z:
        if len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Duplicate ZIP members')
        manifest = json.loads(z.read('capture_report.json'))
        seen, seen_sources = set(), set()
        for entry in manifest['entries']:
            member = PurePosixPath(entry['snapshot_file'])
            if (entry['status'] != 'CAPTURED' or member.parent != PurePosixPath('originals')
                    or member.suffix != '.html' or entry['candidate_id'] in seen):
                raise ValueError('Unsafe or duplicate capture manifest entry')
            seen.add(entry['candidate_id'])
            identity = source_identity(entry['requested_url'])
            if identity in seen_sources or identity[1].split('/')[-1] != str(entry['upstream_job_id']):
                raise ValueError('Duplicate or mismatched source posting identity')
            seen_sources.add(identity)
            raw = z.read(str(member))
            if hashlib.sha256(raw).hexdigest() != entry['sha256'] or len(raw) != entry['bytes']:
                raise ValueError('Capture checksum/size mismatch')
            item = extract(raw, entry)
            item['archive'] = str(archive.resolve())
            result.append(item)
    return result
