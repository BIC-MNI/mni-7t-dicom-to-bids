from pathlib import Path

from bic_util.tsv import upsert_tsv_row


def update_participants_tsv(bids_dataset_path: Path, subject: str):
    """
    Create or update `participants.tsv` with one row for the converted subject.

    Preserve existing columns and rows. Use `n/a` for values of existing columns that are unknown
    for a newly added participant.
    """

    participant_id = f'sub-{subject}'
    print(f"Updating participants.tsv metadata for '{participant_id}'...")
    upsert_tsv_row(bids_dataset_path / 'participants.tsv', 'participant_id', {'participant_id': participant_id})
