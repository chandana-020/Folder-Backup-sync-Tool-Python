import os
import shutil
import argparse
import logging
from datetime import datetime
import zipfile

# -------------------- LOGGING SETUP --------------------
logging.basicConfig(
    filename="backup.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------- COPY FILES --------------------
def copy_files(src, dest, dry_run=False):
    file_count = 0

    for root, dirs, files in os.walk(src):
        rel_path = os.path.relpath(root, src)
        dest_path = os.path.join(dest, rel_path)

        if not os.path.exists(dest_path):
            if not dry_run:
                os.makedirs(dest_path)

        for file in files:
            # Ignore unwanted files
            if file.endswith((".tmp", ".log")) or file == "__pycache__":
                continue

            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, file)

            try:
                # Incremental backup check
                if (not os.path.exists(dest_file) or
                    os.path.getmtime(src_file) > os.path.getmtime(dest_file) or
                    os.path.getsize(src_file) != os.path.getsize(dest_file)):

                    if dry_run:
                        print(f"[DRY RUN] Copy: {src_file} -> {dest_file}")
                    else:
                        shutil.copy2(src_file, dest_file)
                        logging.info(f"Copied: {src_file} -> {dest_file}")
                        print(f"Copied: {file}")
                        file_count += 1

            except Exception as e:
                logging.error(f"Error copying {src_file}: {e}")
                print(f"Error copying {file}: {e}")

    return file_count

# -------------------- ZIP BACKUP --------------------
def zip_backup(folder_path):
    zip_name = folder_path + ".zip"
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    zipf.write(full_path,
                               os.path.relpath(full_path, folder_path))

        print(f"Backup compressed: {zip_name}")
        logging.info(f"Compressed backup: {zip_name}")

    except Exception as e:
        logging.error(f"ZIP Error: {e}")
        print(f"Error during compression: {e}")

# -------------------- ROTATE OLD BACKUPS --------------------
def rotate_backups(dest, keep=3):
    try:
        backups = sorted(
            [d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest, d))]
        )

        if len(backups) > keep:
            to_delete = backups[:-keep]

            for folder in to_delete:
                full_path = os.path.join(dest, folder)
                shutil.rmtree(full_path)
                print(f"Deleted old backup: {folder}")
                logging.info(f"Deleted old backup: {folder}")

    except Exception as e:
        logging.error(f"Rotation Error: {e}")
        print(f"Error in rotation: {e}")

# -------------------- MAIN FUNCTION --------------------
def main():
    parser = argparse.ArgumentParser(description="Folder Backup / Sync Tool")

    parser.add_argument("--source", required=True, help="Source folder path")
    parser.add_argument("--destination", required=True, help="Backup destination path")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--zip", action="store_true", help="Compress backup")
    parser.add_argument("--keep", type=int, default=3, help="Number of backups to keep")

    args = parser.parse_args()

    src = args.source
    dest = args.destination

    # Validate source
    if not os.path.exists(src):
        print("❌ Source folder does not exist!")
        return

    # Ensure destination exists
    os.makedirs(dest, exist_ok=True)

    # Create timestamp folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_folder = os.path.join(dest, f"backup_{timestamp}")

    if not args.dry_run:
        os.makedirs(backup_folder, exist_ok=True)

    print("\n🔄 Starting Backup प्रक्रिया...")
    print(f"📁 Source      : {src}")
    print(f"📂 Destination : {backup_folder}\n")

    # Perform backup
    total_files = copy_files(src, backup_folder, args.dry_run)

    # Optional ZIP
    if args.zip and not args.dry_run:
        zip_backup(backup_folder)

    # Rotate old backups
    rotate_backups(dest, args.keep)

    # Summary
    print("\n✅ Backup Completed Successfully!")
    print("📊 Summary:")
    print(f"   Total files copied : {total_files}")
    print(f"   Backup location    : {backup_folder}")

    logging.info("Backup completed successfully")

# -------------------- RUN --------------------
if __name__ == "__main__":
    main()