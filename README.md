# ORBIT Hermes Agent plugin

Hermes Agent가 자연어 요청과 `hermes orbit` CLI로 Mac Studio의 ComfyUI를 제어하게 만드는 선택 플러그인이다. 공식 Hermes Agent plugin API를 사용하고 ComfyUI `8188` 포트를 직접 공개하지 않는다. 모든 실행은 ORBIT의 사용자 인증, 승인된 워크플로우, 입력 검증, 할당량과 작업 이력을 거친다.

플러그인을 설치하지 않아도 ORBIT 웹 대시보드의 생성 기능은 그대로 사용할 수 있다. 설치하면 “기본 이미지 워크플로로 고양이 그림을 만들고 완료되면 알려줘” 같은 요청을 Hermes가 `orbit_*` 도구로 수행할 수 있다.

## 설치 전 설정

1. 이 폴더를 Hermes 홈의 `plugins/orbit-dashboard/`에 복사한다. 현재 확인한 Windows Desktop 설치에서는 `C:\Users\chozz\AppData\Local\hermes\plugins\orbit-dashboard`다.
2. Hermes가 사용하는 Python 환경에 `keyring>=25,<26`을 설치한다. Hermes plugin doctor가 누락 의존성을 표시한다.
3. Hermes 홈의 `.env`에 다음 두 값을 넣는다. 현재 Windows Desktop 설치에서는 `C:\Users\chozz\AppData\Local\hermes\.env`다.

```dotenv
ORBIT_DASHBOARD_URL=https://orbit.internal.example
ORBIT_DASHBOARD_ORIGIN=https://orbit.internal.example
```

4. `hermes plugins enable orbit-dashboard` 후 gateway를 재시작한다.
5. ORBIT에 로그인해 **이 PC Hermes 등록**을 누른다.

장기 dashboard token은 운영체제 credential store에 저장된다. 플러그인 폴더, Hermes config, 브라우저 localStorage에는 저장하지 않는다. `ORBIT_DASHBOARD_ORIGIN`은 대시보드의 정확한 scheme/host/port와 일치해야 한다.

플러그인은 `127.0.0.1:8765`에 pairing·로컬 첨부 엔드포인트만 연다. Windows 방화벽이나 VPN에 이 포트를 공개하지 않는다. 에이전트가 사용할 실제 기능은 등록된 `orbit_*` 도구이며, 코드·파일 작업은 기존 Hermes 로컬 도구가 계속 담당한다.

대시보드의 음성·문서 첨부를 위해 같은 loopback 서버에 `/v1/orbit/upload`도 제공한다. 허용된 사진·음성·문서 형식만 파일당 25 MB까지 plugin-data의 `uploads/`에 저장하며, 반환된 로컬 경로를 현재 PC의 Hermes Agent가 읽는다. 첨부는 Mac Studio로 업로드되지 않는다.

## 사용할 수 있는 방법

Hermes에게 평소 말하듯 요청하면 등록된 도구를 사용한다.

```text
ORBIT 상태와 사용할 수 있는 워크플로를 확인해줘.
기본 이미지 워크플로로 밤하늘의 고양이를 만들어줘. 완료될 때까지 기다려줘.
방금 만든 결과를 내 다운로드 폴더에 받아줘.
현재 작업이 없다면 ComfyUI 모델을 언로드해줘.
```

터미널에서는 같은 기능을 직접 확인할 수 있다.

```powershell
hermes orbit status
hermes orbit workflows
hermes orbit run image-basic --input 'prompt=밤하늘의 고양이' --input steps=20 --wait
hermes orbit jobs --limit 10
hermes orbit job <job-id> --wait
hermes orbit results <job-id>
hermes orbit download <result-id> .\output.png
hermes orbit free-memory
```

Hermes 대화창과 gateway에서는 `/orbit status`, `/orbit workflows`, `/orbit jobs`도 사용할 수 있다.

## 에이전트 도구

- `orbit_status`: ORBIT 인증, ComfyUI 상태와 큐 확인
- `orbit_list_workflows`: 허용된 워크플로와 입력 스키마 조회
- `orbit_create_job`: 승인된 워크플로 실행
- `orbit_wait_job`: 완료·실패·취소까지 기다리고 결과 조회
- `orbit_list_jobs`, `orbit_get_job`, `orbit_cancel_job`, `orbit_rerun_job`: 작업 관리
- `orbit_list_results`, `orbit_download_result`: 결과 조회와 다운로드
- `orbit_free_comfy_memory`: 관리자가 유휴 상태의 ComfyUI 모델 언로드

`free-memory`는 관리자에게만 허용되고 실행·대기 작업이 있으면 서버가 거절한다. 워크플로 추가·수정과 커스텀 노드 설치는 계속 ORBIT 관리자 화면과 VPN 전용 ComfyUI 편집기에서 수행한다.
