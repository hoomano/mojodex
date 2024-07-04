import os
from datetime import datetime
import requests
import tiktoken

class DocumentChunkManager:

    # Constants
    CHUNK_SIZE = 200  # The target size of each text chunk in tokens
    MIN_CHUNK_SIZE_CHARS = 350  # The minimum size of each text chunk in characters
    MIN_CHUNK_LENGTH_TO_EMBED = 30  # Discard chunks shorter than this
    MAX_NUM_CHUNKS = 10000  # The maximum number of chunks to generate from a text

    def __init__(self):
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # The encoding scheme to use for tokenization
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : __init__ : {e}")

    def _get_text_chunks(self, text, chunk_token_size=None):
        """
        Split a text into chunks of ~CHUNK_SIZE tokens, based on punctuation and newline boundaries.

        Args:
            text: The text to split into chunks.
            chunk_token_size: The target size of each chunk in tokens, or None to use the default CHUNK_SIZE.

        Returns:
            A list of text chunks, each of which is a string of ~CHUNK_SIZE tokens.
        """
        try:
            # Return an empty list if the text is empty or whitespace
            if not text or text.isspace():
                return []

            # Tokenize the text
            tokens = self.tokenizer.encode(text, disallowed_special=())

            # Initialize an empty list of chunks
            chunks = []

            # Use the provided chunk token size or the default one
            chunk_size = chunk_token_size or DocumentChunkManager.CHUNK_SIZE

            # Initialize a counter for the number of chunks
            num_chunks = 0

            # Loop until all tokens are consumed
            while tokens and num_chunks < DocumentChunkManager.MAX_NUM_CHUNKS:
                # Take the first chunk_size tokens as a chunk
                chunk = tokens[:chunk_size]

                # Decode the chunk into text
                chunk_text = self.tokenizer.decode(chunk)

                # Skip the chunk if it is empty or whitespace
                if not chunk_text or chunk_text.isspace():
                    # Remove the tokens corresponding to the chunk text from the remaining tokens
                    tokens = tokens[len(chunk):]
                    # Continue to the next iteration of the loop
                    continue

                # Find the last period or punctuation mark in the chunk
                last_punctuation = max(
                    chunk_text.rfind("."),
                    chunk_text.rfind("?"),
                    chunk_text.rfind("!"),
                    chunk_text.rfind("\n"),
                )

                # If there is a punctuation mark, and the last punctuation index is before MIN_CHUNK_SIZE_CHARS
                if last_punctuation != -1 and last_punctuation > DocumentChunkManager.MIN_CHUNK_SIZE_CHARS:
                    # Truncate the chunk text at the punctuation mark
                    chunk_text = chunk_text[: last_punctuation + 1]

                # Remove any newline characters and strip any leading or trailing whitespace
                chunk_text_to_append = chunk_text.replace("\n", " ").strip()

                if len(chunk_text_to_append) > DocumentChunkManager.MIN_CHUNK_LENGTH_TO_EMBED:
                    # Append the chunk text to the list of chunks
                    chunks.append(chunk_text_to_append)

                # Remove the tokens corresponding to the chunk text from the remaining tokens
                tokens = tokens[len(self.tokenizer.encode(chunk_text, disallowed_special=())):]

                # Increment the number of chunks
                num_chunks += 1

            # Handle the remaining tokens
            if tokens:
                remaining_text = self.tokenizer.decode(tokens).replace("\n", " ").strip()
                if len(remaining_text) > DocumentChunkManager.MIN_CHUNK_LENGTH_TO_EMBED:
                    chunks.append(remaining_text)

            return chunks
        except Exception as e:
            raise Exception(f"_get_text_chunks: {e}")

    def create_document_chunks(self, document_pk, text, embeddeding_function, user_id,
                               user_task_execution_pk=None, task_name_for_system=None,
                               chunk_validation_callback=None, chunk_token_size=None):
        """
        Create a list of document chunks from a document object and return the list of chunks object.

        Args:
            document_pk: The document pk to associate with the chunks.
            text: The text to create chunks from.
            embeddeding_function: The function to use to embed the chunks.
            user_id: The user id to associate with the chunks.
            chunk_validation_callback: Callback to validate chunk before saving it. Returns True if chunk is valid, False otherwise.
            chunk_token_size: The target size of each chunk in tokens, or None to use the default CHUNK_SIZE.

        Returns:
            A list of the document chunks db objects.
            """
        try:
            chunks = self._get_text_chunks(text, chunk_token_size)

            # Insert into PSQL the document chunks
            valid_chunks_pk = []
            for chunk_index in range(len(chunks)):
                if chunk_validation_callback:
                    valid_chunk = chunk_validation_callback(chunks[chunk_index], user_id)
                    if not valid_chunk:
                        continue
                embedding = embeddeding_function(chunks[chunk_index], user_id, user_task_execution_pk, task_name_for_system)
                document_chunk_pk = self.__add_document_chunk_to_db(document_pk, chunk_index, chunks[chunk_index], embedding)
                valid_chunks_pk.append(document_chunk_pk)

            return valid_chunks_pk
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : create_document_chunks : {e}")

    def __add_document_chunk_to_db(self, document_fk, chunk_index, chunk_text, embedding):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/document_chunk"
            pload = {'datetime': datetime.now().isoformat(), 'document_fk': document_fk, 'chunk_index': chunk_index, 'chunk_text': chunk_text, 'embedding': embedding}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.put(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(f"__add_document_chunk_to_db : {internal_request.status_code} - {internal_request.text}")
            document_chunk_pk = internal_request.json()["document_chunk_pk"]
            return document_chunk_pk
        except Exception as e:
            raise Exception(f"__add_document_chunk_to_db : {e}")

    def update_document_chunks(self, document_pk, text, embeddeding_function, user_id, old_chunks_pks,
                               chunk_validation_callback=None, chunk_token_size=None):
        try:
            # 1. Split the text into chunks
            new_chunks = self._get_text_chunks(text, chunk_token_size)
            # 1.1 Validate the new chunks
            new_valid_chunks = [chunk for chunk in new_chunks if chunk_validation_callback(chunk, user_id)]
            # 2. Get the existing chunks of the documents
            # 3. For each existing chunk, modify with the new chunk.
            common_chunks = min(len(old_chunks_pks), len(new_valid_chunks))

            for index in range(common_chunks):
                chunk_pk = old_chunks_pks[index]
                chunk_text = new_valid_chunks[index]
                embedding = embeddeding_function(new_valid_chunks[index], user_id)
                self.__update_document_chunk_in_db(chunk_pk, chunk_text, embedding)

            # if the old list is longer than the new one
            # 4. For each remaining old chunk, delete the chunk
            if len(old_chunks_pks) > len(new_valid_chunks):
                for old_chunk_pk in old_chunks_pks[len(new_valid_chunks):]:
                    self.__delete_document_chunk_in_db(old_chunk_pk)
            # 5. For each remaining new chunk, add the chunk
            else:
                for i in range(common_chunks, len(new_valid_chunks)):
                    new_embeddeding = embeddeding_function(new_valid_chunks[i], user_id)
                    document_chunk_pk = self.__add_document_chunk_to_db(document_pk, i, new_valid_chunks[i], new_embeddeding)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : update_document_chunks : {e}")

    def __update_document_chunk_in_db(self, chunk_pk, chunk_text, embedding):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/document_chunk"
            pload = {'datetime': datetime.now().isoformat(), 'chunk_pk': chunk_pk,
                     'chunk_text': chunk_text, 'embedding': embedding}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(f"__update_document_chunk_in_db : {internal_request.status_code} - {internal_request.text}")
            document_chunk_pk = internal_request.json()["document_chunk_pk"]
            return document_chunk_pk
        except Exception as e:
            raise Exception(f"__update_document_chunk_in_db : {e}")

    def __delete_document_chunk_in_db(self, chunk_pk):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/document_chunk"
            pload = {'datetime': datetime.now().isoformat(), 'chunk_pk': chunk_pk}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.delete(uri, data=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(
                    f"__delete_document_chunk_in_db : {internal_request.status_code} - {internal_request.text}")
            document_chunk_pk = internal_request.json()["document_chunk_pk"]
            return document_chunk_pk
        except Exception as e:
            raise Exception(f"__delete_document_chunk_in_db : {e}")