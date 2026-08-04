"""
CLI для batch processor

Использование:
    python -m backend.archive.cli process-folder <folder_path> [--name <episode_name>]
    python -m backend.archive.cli process-person <folder_path> <person_name>
    python -m backend.archive.cli process-all <dataset_folder>
"""

import argparse
import json
import sys
import asyncio
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.archive import ArchiveProcessor, PersonIntakePipeline, BatchArchiveProcessor


def process_folder(args):
    """Обработать папку с фото"""
    processor = ArchiveProcessor()
    result = processor.process_folder(args.folder, args.name)
    
    # Сохранение результатов
    output_path = Path(args.output) / f"{Path(args.folder).name}_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"Results saved to {output_path}")
    print(f"Photos: {len(result.get('photos', []))}")
    print(f"Faces: {len(result.get('faces', []))}")
    print(f"Clusters: {len(result.get('clusters', {}).get('clusters', {}))}")
    
    return result


def process_person(args):
    """Обработать папку персонала"""
    pipeline = PersonIntakePipeline()
    result = pipeline.process_folder(args.folder, args.name)
    
    # Сохранение отчёта
    output_path = Path(args.output) / f"{Path(args.folder).name}_intake.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"Intake report saved to {output_path}")
    print(f"Photos processed: {result.get('photos_processed', 0)}")
    print(f"Embeddings generated: {result.get('embeddings_generated', 0)}")
    
    return result


async def process_all_async(args):
    """Обработать всю папку с датасетом (async)"""
    # Импорт Prisma (если доступен)
    try:
        from prisma import Prisma
        prisma = Prisma()
        await prisma.connect()
    except Exception:
        prisma = None
    
    processor = BatchArchiveProcessor(prisma_client=prisma)
    dataset = Path(args.dataset)
    
    for folder in sorted(dataset.iterdir()):
        if folder.is_dir():
            print(f"Processing {folder.name}...")
            result = processor.process_folder(str(folder))
            
            # Сохранение
            output_path = Path(args.output) / f"{folder.name}_batch.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str)
    
    if prisma:
        await prisma.disconnect()


def process_all(args):
    """Обработать всю папку с датасетом"""
    asyncio.run(process_all_async(args))


async def main_async():
    parser = argparse.ArgumentParser(description="Batch Archive Processor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # process-folder
    p_folder = subparsers.add_parser("process-folder", help="Обработать папку с фото")
    p_folder.add_argument("folder", help="Путь к папке")
    p_folder.add_argument("--name", help="Имя эпизода (опционально)")
    p_folder.add_argument("--output", default="batch_output", help="Папка для результатов")
    
    # process-person
    p_person = subparsers.add_parser("process-person", help="Обработать папку персонала")
    p_person.add_argument("folder", help="Путь к папке")
    p_person.add_argument("name", help="Имя персоны")
    p_person.add_argument("--output", default="batch_output", help="Папка для результатов")
    
    # process-all
    p_all = subparsers.add_parser("process-all", help="Обработать весь датасет")
    p_all.add_argument("dataset", help="Путь к датасету")
    p_all.add_argument("--output", default="batch_output", help="Папка для результатов")
    
    args = parser.parse_args()
    
    if args.command == "process-folder":
        process_folder(args)
    elif args.command == "process-person":
        process_person(args)
    elif args.command == "process-all":
        await process_all_async(args)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Batch Archive Processor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # process-folder
    p_folder = subparsers.add_parser("process-folder", help="Обработать папку с фото")
    p_folder.add_argument("folder", help="Путь к папке")
    p_folder.add_argument("--name", help="Имя эпизода (опционально)")
    p_folder.add_argument("--output", default="batch_output", help="Папка для результатов")
    
    # process-person
    p_person = subparsers.add_parser("process-person", help="Обработать папку персонала")
    p_person.add_argument("folder", help="Путь к папке")
    p_person.add_argument("name", help="Имя персоны")
    p_person.add_argument("--output", default="batch_output", help="Папка для результатов")
    
    # process-all
    p_all = subparsers.add_parser("process-all", help="Обработать весь датасет")
    p_all.add_argument("dataset", help="Путь к датасету")
    p_all.add_argument("--output", default="batch_output", help="Папка для результатов")
    
    args = parser.parse_args()
    
    if args.command == "process-folder":
        process_folder(args)
    elif args.command == "process-person":
        process_person(args)
    elif args.command == "process-all":
        asyncio.run(process_all_async(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
