import csv
from pathlib import Path
from typing import cast

from bic_util.util import find


class ParticipantsTsvError(ValueError):
    """
    Error raised when `participants.tsv` cannot be safely updated.
    """


def update_participants_tsv(bids_dataset_path: Path, subject: str):
    """
    Create or update `participants.tsv` with one row for the converted subject.

    Preserve existing columns and rows. Use `n/a` for values of existing columns that are unknown
    for a newly added participant.
    """

    file_path = bids_dataset_path / 'participants.tsv'
    participant_id = f'sub-{subject}'

    if file_path.exists():
        print("File 'participants.tsv' already exists.")
        with file_path.open(encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file, delimiter='\t')
            columns = reader.fieldnames
            participants = [cast(dict[str, str], participant) for participant in reader]
    else:
        print("Creating file 'participants.tsv'...")
        columns = ['participant_id']
        participants: list[dict[str, str]] = []

    if columns is None or columns[0] != 'participant_id':
        raise ParticipantsTsvError(f"Expected the first column of '{file_path}' to be 'participant_id'.")

    participant = find(lambda participant: participant['participant_id'] == participant_id, participants)
    if participant is not None:
        print(f"Participant '{participant_id}' already exists in 'participants.tsv'. Skipping.")
        return

    print(f"Adding participant '{participant_id}' to 'participants.tsv'...")
    participants.append({
        column: participant_id if column == 'participant_id' else 'n/a'
        for column in columns
    })

    with file_path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(participants)
