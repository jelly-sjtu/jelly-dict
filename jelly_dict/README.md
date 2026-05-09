# jelly dict

macOS용 영어/일본어 단어 정리 앱. 개인 학습용.

## 개발 환경

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
playwright install webkit
```

## 실행

```bash
python -m app.main
```

## 테스트

```bash
pytest
```

## 설계 문서

[../dev.md](../dev.md)
