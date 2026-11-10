#!/usr/bin/env python3
"""Independent static OpenAPI/authorization/type checks. NOT actual HTTP/DB provider tests."""
from pathlib import Path
from collections import defaultdict,Counter
import json,re,sys,copy,argparse
try:
    import jsonschema
except ImportError:
    print('MISSING jsonschema; run CI pip install jsonschema==4.26.0');sys.exit(2)

ROOT=Path(__file__).resolve().parents[1]

def inspect(root, thorough=True):
    errors=[];checks=0;details=defaultdict(int)
    def ck(condition,label):
        nonlocal checks
        checks+=1
        if not condition:errors.append(label)
    inv=json.loads((root/'docs/architecture/API_INVENTORY.json').read_text())['operations']
    ck(len(inv)==100,'100 typed candidate operations with owner-specific gaps addressed')
    ck(len({x['operation_id'] for x in inv})==len(inv),'no duplicate operation ID')
    ck(len({(x['path'],x['method']) for x in inv})==len(inv),'no duplicate verb/path')
    for owner in 'ABI':
        o=[x for x in inv if x['owner']==owner]
        spec=json.loads((root/f'contracts/openapi/{owner.lower()}-v1.openapi.json').read_text())
        ck(spec['openapi']=='3.1.0',owner+' OpenAPI version')
        comps=spec['components']['schemas'];ck(bool(comps),owner+' has actual component schemas')
        paths=spec['paths'];found=[]
        for path,verbs in paths.items():
            ck(path.startswith('/'),owner+' valid path '+path)
            ck(bool(re.fullmatch(r'/[A-Za-z0-9_{}./-]+',path)),owner+' templated path syntax '+path)
            for method,z in verbs.items():
                found.append((method.upper(),path,z['operationId']))
                details['operations']+=1
                operation=next((x for x in o if x['operation_id']==z['operationId']),None)
                ck(operation is not None,owner+' corresponding inventory operation '+z['operationId'])
                if operation is None:continue
                ck((operation['method'],operation['path'])==(method.upper(),path),owner+' stable inventory path '+z['operationId'])
                params=z.get('parameters',[])
                template=re.findall(r'{([^{}]+)}',path)
                present=[p['name'] for p in params if p.get('in')=='path']
                ck(Counter(template)==Counter(present),'MISSING_OR_EXTRA_PATH_PARAMETER '+z['operationId'])
                ck(all(p.get('required') is True and isinstance(p.get('schema'),dict) and p['schema'].get('type')=='string' for p in params if p.get('in')=='path'),'PATH_PARAMETER_REQUIRED '+z['operationId'])
                ck(len({(p['name'],p['in']) for p in params})==len(params),'DUPLICATE_PARAMETER '+z['operationId'])
                for reqparam in operation.get('required_query',[]):
                    ck(any(p['in']=='query' and p['name']==reqparam and p.get('required') is True for p in params),'REQUIRED_QUERY_PARAMETER '+z['operationId']+':'+reqparam)
                auth=operation['auth']
                expected={
                    'admin':[{'AdminSession':[]}], 'service':[{'ServiceToken':[]}],
                    'staff':[{'StaffSession':[]}],
                    'admin_or_service':[{'AdminSession':[]},{'ServiceToken':[]}],
                    'admin_or_staff':[{'AdminSession':[]},{'StaffSession':[]}],
                    'admin_staff_or_service':[{'AdminSession':[]},{'StaffSession':[]},{'ServiceToken':[]}]
                }[auth]
                ck(z.get('security')==expected,'ACTOR_SECURITY '+z['operationId'])
                policy=z.get('x-auth-policy',{})
                ck(policy.get('actor_class')==auth and policy.get('deny_unscoped') is True and policy.get('resource_ownership_check') is True,'ACTOR_POLICY '+z['operationId'])
                if auth in ('admin_or_service','service','admin_staff_or_service'):
                    ck(policy.get('required_service_scope')==operation.get('service_scope') and bool(operation.get('service_scope')),'SERVICE_SCOPE '+z['operationId'])
                if auth in ('staff','admin_or_staff','admin_staff_or_service'):ck(policy.get('required_staff_scope')==operation.get('staff_scope') and bool(operation.get('staff_scope')),'STAFF_SCOPE '+z['operationId'])
                if auth in ('admin_or_staff','admin_staff_or_service'):ck(policy.get('staff_activation_stage')==22,'STAFF_ACTIVATION_STAGE '+z['operationId'])
                if z.get('x-contract-status')!='TYPED_CANDIDATE_AWAITING_PROVIDER_TEST':ck(False,'FALSE_FROZEN_STATUS '+z['operationId'])
                response=z.get('responses',{})
                successes={c:x for c,x in response.items() if c.isdigit() and c.startswith('2')}
                ck(bool(successes),'MISSING_SUCCESS_RESPONSE '+z['operationId'])
                ck(bool(all('content' in x and len(x['content'])==1 for x in successes.values())),'UNTYPED_SUCCESS_RESPONSE '+z['operationId'])
                for status,ret in successes.items():
                    details['typed_success_responses']+=1
                    if not ret.get('content'):continue
                    media,body=next(iter(ret['content'].items()))
                    schema=body.get('schema')
                    ck(isinstance(schema,dict),'MISSING_RESPONSE_SCHEMA '+z['operationId']+':'+status)
                    if not isinstance(schema,dict):continue
                    if media in ('application/octet-stream','application/pdf'):
                        ck(schema.get('type')=='string' and schema.get('format')=='binary','UNTYPED_BINARY '+z['operationId'])
                        if z['operationId']=='downloadPaperPdf':ck(media=='application/pdf','PAPER_PDF_CONTENT_TYPE')
                    else:
                        ck(media=='application/json','JSON_SUCCESS_MEDIA '+z['operationId'])
                        ck(schema.get('type')=='object' and schema.get('additionalProperties') is False and 'data' in schema.get('required',[]) and 'request_id' in schema.get('required',[]),'UNTYPED_SUCCESS_ENVELOPE '+z['operationId'])
                        ref=schema.get('properties',{}).get('data',{}).get('$ref','')
                        ck(ref.startswith('#/components/schemas/') and ref.split('/')[-1] in comps,'UNTYPED_SUCCESS_DATA '+z['operationId'])
                        ck('additionalProperties' not in schema.get('properties',{}).get('data',{}),'NO_OPEN_DATA '+z['operationId'])
                    if thorough:
                        try:jsonschema.Draft202012Validator.check_schema({'$defs':comps,'type':'object','properties':{'output':schema}})
                        except Exception as ex:ck(False,'INVALID_SUCCESS_JSON_SCHEMA '+z['operationId']+':'+str(ex)[:70])
                for status in ('401','403','409','422','503'):
                    bad=response.get(status,{}).get('content',{}).get('application/json',{}).get('schema',{})
                    ck(bad.get('$ref')=='#/components/schemas/ErrorEnvelope','UNSTRUCTURED_ERROR_RESPONSE '+z['operationId']+':'+status)
                if method.upper()=='GET':ck('requestBody' not in z,'UNEXPECTED_GET_BODY '+z['operationId'])
                if 'requestBody' in z:
                    b=z['requestBody']
                    ck(b.get('required') is True and len(b.get('content',{}))==1,'BODY_REQUIRED '+z['operationId'])
                    for media,content in b.get('content',{}).items():
                        ref=content.get('schema',{}).get('$ref','')
                        ck(ref=='#/components/schemas/'+z['operationId']+'Request','UNTYPED_REQUEST '+z['operationId'])
                        if ref.startswith('#/components/schemas/') and ref.split('/')[-1] in comps:
                            ms=comps[ref.split('/')[-1]]
                            ck(ms.get('type')=='object' and ms.get('additionalProperties') is False and bool(ms.get('properties')),'OPEN_REQUEST_SCHEMA '+z['operationId'])
                ck(z.get('x-contract-status')=='TYPED_CANDIDATE_AWAITING_PROVIDER_TEST','DRAFT_GATE '+z['operationId'])
        expect={(x['method'],x['path'],x['operation_id']) for x in o}
        ck(set(found)==expect and len(found)==len(expect),'OWNER_API_COVERAGE_'+owner)
        if thorough:
            for name,model in comps.items():
                try:jsonschema.Draft202012Validator.check_schema(model)
                except Exception as ex:ck(False,'INVALID_COMPONENT_SCHEMA '+owner+':'+name+':'+str(ex)[:70])
        if owner=='A':
            ck('/vault/v1/shells/{shell_id}/materials' in paths,'A_S1_LIST_MATERIALS')
        if owner=='I':
            for p in ('/link/v1/courses/{course_id}/materials','/link/v1/courses/{course_id}/search','/link/v1/courses/{course_id}/materials/{material_id}/download'):
                ck(p in paths,'I_S4_MATERIAL_PROXY '+p)
        if owner=='B':
            z=paths['/core/v1/staff/{staff_id}/permissions']['get']
            ck(z.get('security')==[{'ServiceToken':[]}], 'B_STAFF_LOOKUP_SERVICE_ONLY')
            ck(paths['/core/v1/me/permissions']['get']['security']==[{'StaffSession':[]}], 'B_STAFF_SELF_STAFF_ONLY')
            ck(paths['/core/v1/students']['get']['responses']['200']['content']['application/json']['schema']['properties']['data']['$ref'].endswith('StudentList'),'B_SYNTHETIC_LIST_RESPONSE')
    # Ensure teacher endpoint never allows admin impersonation and needs a course query.
    ispec=json.loads((root/'contracts/openapi/i-v1.openapi.json').read_text())
    teacher=ispec['paths']['/link/v1/teacher/content']['get']
    ck(teacher['security']==[{'StaffSession':[]}], 'I_TEACHER_ONLY_STAFF_SESSION')
    ck(any(p['name']=='course_id' and p['in']=='query' and p['required'] for p in teacher['parameters']), 'I_TEACHER_COURSE_REQUIRED')
    # Specific ownership and semantic requirements: no generic response object and no credential leak.
    bspec=json.loads((root/'contracts/openapi/b-v1.openapi.json').read_text())
    provider=bspec['components']['schemas']['AiProvider']
    ck('secret_value' not in provider.get('properties',{}),'SECRET_VALUE_IN_PROVIDER_RESPONSE')
    ck(all(k in bspec['components']['schemas']['GradeEvent']['properties'] for k in ('reason','corrects_event_id','expected_prior_revision')),'GRADE_CORRECTION_FIELDS')
    return checks,errors,dict(details)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(ROOT));p=parser.parse_args()
    checks,errors,details=inspect(Path(p.root))
    print(json.dumps({'result':'PASS' if not errors else 'FAIL','checks':checks,'failures':len(errors),'examples':errors[:45],'details':details,'disclaimer':'Typed OpenAPI structural/spec QA only, zero real service tests'},ensure_ascii=False,indent=2))
    sys.exit(bool(errors))
