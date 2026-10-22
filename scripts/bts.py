"""BTS form vocabulary, field validation, review reports and safe HTML sections."""
from __future__ import annotations
import html
import re
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urlsplit

SECTIONS = {
 'Program Overview': {'program_title':'Program Title','degree_level':'Degree Level','school_name':'School Name','program_link':'Program Link','contact_university':'Contact (University)'},
 'Degree and Academic Information': {'degree_type':'Degree Type'},
 'Areas of Study': {'areas_of_study':'Areas of Study','primary_area_of_study':'Primary Area of Study (BTS category)','additional_areas_of_study':'Additional Areas of Study (BTS categories)'},
 'Program Description': {'description_html':'Description'},
 'Location': {**{f'{scope}_{part}':f'{scope.title()} {part.replace("_"," ").title()}' for scope in ('university','program') for part in ('street','street_2','postal_code','city','region','country','latitude','longitude')},'inherit_university_location':'Inherit university location'},
 'Study Format and Duration': {'format':'Format','attendance':'Attendance','duration_original':'Published duration','duration_bts':'BTS duration choice'},
 'Annual Tuition and Fee Year': {'tuition_home':'Annual home tuition','tuition_non_eu':'Annual non-EU / overseas tuition','tuition_currency':'Original tuition currency','tuition_academic_year':'Tuition academic year','tuition_source_url':'Tuition source URL','tuition_last_verified':'Tuition last verified','tuition_billing_period':'Tuition billing period','tuition_conversion':'EUR conversion (only when needed)'},
 'Application Deadlines': {'application_deadline':'Application Deadline','application_deadline_date':'Application Deadline Date','scholarship_deadline':'Scholarship consideration deadline','final_admission_deadline':'Final admission deadline','application_opening_date':'Application opening date','expected_start_date':'Expected start date','start_application_url':'Start Your Application URL'},
 'Admissions Requirements': {'admissions_requirements':'Admissions Requirements','admissions_difficulty':'Admissions Difficulty (BTS editorial)','minimum_gpa':'Minimum GPA'},
 'English Language Requirements': {'english_proficiency_required':'English Proficiency Required (non-US)','english_tests':'English tests and scores'},
 'Tests and Special Requirements': {'entrance_exam':'Entrance Exam','gmat_gre_required':'GMAT/GRE Required','sat_act_required':'SAT / ACT Required','aps_required':'APS Required'},
 'Additional Program Flags': {key:label for key,label in [('numerus_fixus','Numerus Fixus'),('pre_master','Pre-Master'),('foundation_year','Foundation Year'),('post_bachelor_work_experience','Post-Bachelor Work Experience'),('erasmus_mundus','Erasmus Mundus'),('american_school','American School'),('franchise','Franchise'),('spring_intake','Spring Intake'),('internship_built_in','Internship Built In')]},
}
LABELS={k:v for fields in SECTIONS.values() for k,v in fields.items()}
FLAGS={'inherit_university_location','english_proficiency_required','entrance_exam','gmat_gre_required','sat_act_required','numerus_fixus','pre_master','foundation_year','post_bachelor_work_experience','erasmus_mundus','american_school','franchise','spring_intake','internship_built_in'}
URL_FIELDS={'program_link','tuition_source_url','start_application_url'}
DATE_FIELDS={'tuition_last_verified','application_deadline_date','scholarship_deadline','final_admission_deadline','application_opening_date','expected_start_date'}
DURATION_CHOICES={'Less than 1 year','1 year','1.5 years','Less than 2 years','2 years','2.5 years','3 years','3.5 years','4 years','More than 4 years'}
REQUIRED={'program_title','degree_level','program_link','degree_type','areas_of_study','description_html','format','duration_original','duration_bts','tuition_home','tuition_non_eu','tuition_currency','tuition_academic_year','tuition_source_url','tuition_last_verified','tuition_billing_period','admissions_requirements'}

class DescriptionParser(HTMLParser):
    allowed={'h3','h4','p','ul','li','strong','em'}
    def __init__(self):
        super().__init__();self.stack=[];self.seen=False
    def handle_starttag(self,tag,attrs):
        if tag not in self.allowed or attrs: raise ValueError('Description HTML contains unsupported tags or attributes')
        self.stack.append(tag);self.seen=True
    def handle_endtag(self,tag):
        if not self.stack or self.stack.pop()!=tag: raise ValueError('Unbalanced description HTML')
    def handle_entityref(self,name): pass
    def handle_charref(self,name): pass
    def close(self):
        super().close()
        if self.stack or not self.seen: raise ValueError('Incomplete description HTML')

def validate_bts(record,evidence):
    data=record['bts_fields']
    if set(data)!=set(LABELS): raise ValueError(f"{record['id']}: BTS form field coverage mismatch")
    for key,field in data.items():
        value,status=field['value'],field['status']
        if (value is not None)!=(status=='verified'): raise ValueError(f'{key}: verified value/status mismatch')
        if status=='verified' and not field['evidence']: raise ValueError(f'{key}: missing evidence')
        if status=='conflicting' and not field['review_note']: raise ValueError(f'{key}: conflicting value requires review note')
        if key in FLAGS and value is not None and not isinstance(value,bool): raise ValueError(f'{key}: expected boolean or unknown')
        if key in URL_FIELDS and value is not None:
            u=urlsplit(value)
            if u.scheme!='https' or not u.hostname: raise ValueError(f'{key}: invalid HTTPS URL')
        if key in DATE_FIELDS and value is not None: date.fromisoformat(value)
        if key=='duration_bts' and value is not None and value not in DURATION_CHOICES: raise ValueError('Unsupported BTS duration')
        for item in field['evidence']:
            src=evidence.get(item['source_id'])
            if src is None or src['access_status']!='accessible' or not src['url'].startswith('https://') or not (urlsplit(src['url']).hostname == record['fields']['university_identity']['value'] or (urlsplit(src['url']).hostname or '').endswith('.' + record['fields']['university_identity']['value'])): raise ValueError(f'{key}: invalid source')
            if src['accessed_on']>field['verified_on'] or field['verified_on']>record['verification_date']: raise ValueError(f'{key}: invalid evidence date')
        if key=='description_html' and value is not None:
            parser=DescriptionParser();parser.feed(value);parser.close()
    def val(key):return data[key]['value']
    old=record['fields']
    if val('program_title')!=old['program_title']['value'] or val('degree_type')!=old['qualification']['value'] or val('program_link')!=old['source_url']['value']: raise ValueError('BTS identity must match source record')
    if val('degree_level') != {'undergraduate':'Bachelors','postgraduate_masters':'Masters'}[old['degree_level']['value']]: raise ValueError('Incorrect degree classification')
    if val('tuition_source_url') and not any(evidence[e['source_id']]['url']==val('tuition_source_url') for e in data['tuition_source_url']['evidence']): raise ValueError('Tuition source URL lacks matching evidence')
    if val('minimum_gpa') and val('minimum_gpa')['minimum']>val('minimum_gpa')['scale']: raise ValueError('GPA exceeds grading scale')
    for key in ('program_title','degree_level','program_link','degree_type'):
        if val(key) is None: raise ValueError(f'{key}: core identity required')
    if val('tuition_non_eu') is not None:
        t=val('tuition_non_eu')
        if t['period']!='year' or t['fee_status']!='Overseas' or t['academic_year']!=val('tuition_academic_year'): raise ValueError('Annual overseas tuition scope mismatch')
        if t['amount']!=old['international_tuition']['value']['amount']: raise ValueError('Overseas tuition differs from sourced record')
    if val('tuition_home') is not None and (val('tuition_home')['period']!='year' or val('tuition_home')['academic_year']!=val('tuition_academic_year')): raise ValueError('Annual home tuition scope mismatch')
    dur=val('duration_original')
    if dur is not None and val('duration_bts') is not None:
        months=dur['amount']*(12 if dur['unit']=='years' else 1)
        exact={12:'1 year',18:'1.5 years',24:'2 years',30:'2.5 years',36:'3 years',42:'3.5 years',48:'4 years'}.get(months)
        if exact and val('duration_bts')!=exact: raise ValueError('BTS duration does not match published duration')
        if not exact and months >= 24 and months <= 48: raise ValueError('Duration needs manual dropdown review')
    if val('application_deadline_date') and val('final_admission_deadline') and val('application_deadline_date')!=val('final_admission_deadline'): raise ValueError('Scholarship and final deadline conflated')

def completeness(record):
    data=record['bts_fields'];counts={s:sum(f['status']==s for f in data.values()) for s in ('verified','unverified','conflicting','not_published','not_applicable','manual_evidence_required')}
    needs=[k for k,f in data.items() if f['status']!='verified' or f['human_review_status']!='reviewed']
    return {'program_id':record['id'],'total_fields':len(data),'verified_fields':counts['verified'],'missing_fields':sum(counts[s] for s in ('unverified','not_published','manual_evidence_required')),'conflicting_fields':counts['conflicting'],'fields_requiring_human_review':len(needs),'review_field_names':needs,'completeness_percent':round(100*counts['verified']/len(data),1),'notice':'Completeness measures populated sourced fields, not accuracy or approval.'}

def render_bts(record,evidence):
    out=[]
    for section,items in SECTIONS.items():
        out.append(f'<section><h2>{html.escape(section)}</h2><dl>')
        for key,label in items.items():
            f=record['bts_fields'][key];v=f['value'] if f['status']=='verified' else None
            if key=='description_html' and v is not None: rendered=v
            elif isinstance(v,bool): rendered='Yes' if v else 'No'
            elif isinstance(v,dict) and 'fee_status' in v: rendered=html.escape(f"{v['currency']} {v['amount']:,} per {v['period']}; {v['academic_year']}; {v['fee_status']} fee status. {v['note']}")
            elif isinstance(v,dict) and key=='duration_original': rendered=html.escape(f"{v['amount']} {v['unit']}")
            elif isinstance(v,dict) and key=='minimum_gpa': rendered=html.escape(f"{v['minimum']} out of {v['scale']}; {v['context']}")
            elif isinstance(v,dict): rendered=html.escape(', '.join(f'{k}: {value}' for k,value in v.items()))
            elif isinstance(v,list): rendered=html.escape(', '.join(map(str,v)))
            elif v is None: rendered='Not verified — no confirmed value' if f['status'] in ('unverified','manual_evidence_required','conflicting') else html.escape(f['status'].replace('_',' ').title())
            else: rendered=html.escape(str(v))
            if key in URL_FIELDS and v is not None: rendered=f'<a href="{html.escape(v,quote=True)}">{rendered}</a>'
            sources=''.join('<li><a href="'+html.escape(evidence[e['source_id']]['url'],quote=True)+'">'+html.escape(evidence[e['source_id']]['title'])+'</a> — '+html.escape(e['locator'])+'</li>' for e in f['evidence'])
            out.append(f'<dt>{html.escape(label)}</dt><dd><div>{rendered}</div><small>Status: {html.escape(f["status"])}; human review: {html.escape(f["human_review_status"])}; checked {html.escape(f["verified_on"])}. {html.escape(f["review_note"])}</small><ul>{sources}</ul></dd>')
        out.append('</dl></section>')
    out.append('<section><h2>Official Sources and Verification Status</h2><p>Source links and review states are listed beside every field. Original university source: <a href="'+html.escape(record['fields']['source_url']['value'],quote=True)+'">'+html.escape(record['fields']['source_url']['value'])+'</a>.</p></section>')
    return ''.join(out)
