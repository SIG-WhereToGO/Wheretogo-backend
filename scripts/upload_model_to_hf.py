"""
hf에 모델 업로드 할때 쓴 스크립트. 
"""
import argparse

from huggingface_hub import HfApi, create_repo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local_dir", required=True, help="로컬 모델 폴더 경로 (config.json, pytorch_model.bin/safetensors, tokenizer 파일 등이 있는 곳)")
    parser.add_argument("--repo_id", required=True, help="예: your-hf-id/klue-roberta-travel-tag")
    parser.add_argument("--private", action="store_true", help="비공개 repo로 생성 (테스트용이면 켜는 걸 추천)")
    args = parser.parse_args()

    api = HfApi()
    create_repo(args.repo_id, private=args.private, exist_ok=True)

    api.upload_folder(
        folder_path=args.local_dir,
        repo_id=args.repo_id,
        repo_type="model",
    )
    print(f"업로드 완료: https://huggingface.co/{args.repo_id}")
    print("private repo라면, 배포 환경에서 HF_TOKEN 환경변수(읽기 권한 토큰)를 함께 설정해야 다운로드됩니다.")


if __name__ == "__main__":
    main()
