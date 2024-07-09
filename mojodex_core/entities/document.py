
from mojodex_core.embedder.embedding_service import EmbeddingService
from mojodex_core.entities.db_base_entities import MdDocument
from sqlalchemy.orm import object_session
from datetime import datetime, timezone

from mojodex_core.entities.document_chunk import DocumentChunk

class Document(MdDocument):

    # Constants
    CHUNK_SIZE = 200  # The target size of each text chunk in tokens
    MIN_CHUNK_SIZE_CHARS = 350  # The minimum size of each text chunk in characters
    MIN_CHUNK_LENGTH_TO_EMBED = 30  # Discard chunks shorter than this
    MAX_NUM_CHUNKS = 10000  # The maximum number of chunks to generate from a text

    @property
    def chunks(self) -> list[DocumentChunk]:
        """
        Return the list of chunks of the document.
        """
        try:
            session = object_session(self)
            return session.query(DocumentChunk).\
                filter(DocumentChunk.document_fk == self.document_pk).\
                order_by(DocumentChunk.index).all()
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: chunks :: {e}")
        
    @property
    def text(self):
        """
        Return the text of the document.
        """
        try:
            chunk_text = " ".join([chunk[0] for chunk in self.chunks]) if self.chunks else ""
            return chunk_text
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: text :: {e}")
        
    def update(self, new_text: str, chunk_validation_callback=None):
        """
        Update the document with the new text.
        """
        try:
            # For now, we consider the author of the document is the only one who can update it
            # This could be changed in the future
            self._update_chunks(new_text, self.author_user_id, chunk_validation_callback=chunk_validation_callback)
            self.last_update_date = datetime.now(timezone.utc)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: update_document : {e}")
        
    def _update_chunks(self, new_text, user_id, chunk_validation_callback=None, chunk_token_size=None):
        """
        Update the document chunks with the new text.
        """
        try:
            # 1. Split the text into chunks
            new_chunks_text = self._split_text_in_chunks(new_text, chunk_token_size)
            # 1.1 Validate the new chunks
            new_valid_chunks_text = [chunk for chunk in new_chunks_text if chunk_validation_callback(chunk, user_id)] if chunk_validation_callback is not None else new_chunks
            # 2. Get the existing chunks of the documents
            # 3. For each existing chunk, modify with the new chunk.
            old_chunks = self.chunks.copy()
            common_chunks = min(len(old_chunks), len(new_valid_chunks_text))

            for index in range(common_chunks):
                old_chunk = old_chunks[index]
                new_chunk_text = new_valid_chunks_text[index]
                embedding = EmbeddingService().embed(new_valid_chunks_text[index], user_id)
                old_chunk.update(new_chunk_text, embedding)

            # if the old list is longer than the new one
            # 4. For each remaining old chunk, delete the chunk
            if len(old_chunks) > len(new_valid_chunks_text):
                for old_chunk in old_chunks[len(new_valid_chunks_text):]:
                    old_chunk.delete()
            # 5. For each remaining new chunk, add the chunk
            else:
                for i in range(common_chunks, len(new_valid_chunks_text)):
                    new_embeddeding = EmbeddingService().embed(new_valid_chunks_text[i], user_id)
                    self._add_document_chunk_to_db(i, new_valid_chunks_text[i], new_embeddeding)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : update_document_chunks : {e}")
          
    def _split_text_in_chunks(self, text: str, chunk_token_size=None):
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
            tokens = EmbeddingService().tokenizer.encode(text, disallowed_special=())

            # Initialize an empty list of chunks
            chunks = []

            # Use the provided chunk token size or the default one
            chunk_size = chunk_token_size or self.CHUNK_SIZE

            # Initialize a counter for the number of chunks
            num_chunks = 0

            # Loop until all tokens are consumed
            while tokens and num_chunks < self.MAX_NUM_CHUNKS:
                # Take the first chunk_size tokens as a chunk
                chunk = tokens[:chunk_size]

                # Decode the chunk into text
                chunk_text = EmbeddingService().tokenizer.decode(chunk)

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
                if last_punctuation != -1 and last_punctuation > self.MIN_CHUNK_SIZE_CHARS:
                    # Truncate the chunk text at the punctuation mark
                    chunk_text = chunk_text[: last_punctuation + 1]

                # Remove any newline characters and strip any leading or trailing whitespace
                chunk_text_to_append = chunk_text.replace("\n", " ").strip()

                if len(chunk_text_to_append) > self.MIN_CHUNK_LENGTH_TO_EMBED:
                    # Append the chunk text to the list of chunks
                    chunks.append(chunk_text_to_append)

                # Remove the tokens corresponding to the chunk text from the remaining tokens
                tokens = tokens[len(EmbeddingService().tokenizer.encode(chunk_text, disallowed_special=())):]

                # Increment the number of chunks
                num_chunks += 1

            # Handle the remaining tokens
            if tokens:
                remaining_text = EmbeddingService().tokenizer.decode(tokens).replace("\n", " ").strip()
                if len(remaining_text) > self.MIN_CHUNK_LENGTH_TO_EMBED:
                    chunks.append(remaining_text)

            return chunks
        except Exception as e:
            raise Exception(f"_get_text_chunks: {e}")

    def create_document_chunks(self, text: str, user_id,
                               user_task_execution_pk=None, task_name_for_system=None,
                               chunk_validation_callback=None, chunk_token_size=None):
        """
        Create a list of document chunks and return the list of chunks object.

        Args:
            text: The text to create chunks from.
            user_id: The user id to associate with the chunks.
            user_task_execution_pk: The user task execution pk to associate with the llm calls.
            task_name_for_system: The task name to associate with the llm calls.
            chunk_validation_callback: Callback to validate chunk before saving it. Returns True if chunk is valid, False otherwise.
            chunk_token_size: The target size of each chunk in tokens, or None to use the default CHUNK_SIZE.
            """
        try:
            chunks = self._split_text_in_chunks(text, chunk_token_size)

            # Insert into PSQL the document chunks
            for chunk_index in range(len(chunks)):
                if chunk_validation_callback:
                    valid_chunk = chunk_validation_callback(chunks[chunk_index], user_id)
                    if not valid_chunk:
                        continue
                embedding = EmbeddingService().embed(chunks[chunk_index], user_id, user_task_execution_pk, task_name_for_system)
                self._add_document_chunk_to_db(chunk_index, chunks[chunk_index], embedding)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : create_document_chunks : {e}")
        
    def _add_document_chunk_to_db(self, chunk_index, chunk_text, embedding):
        """
        Add a document chunk to the database.
        """
        try:
            session = object_session(self)
            chunk_db = DocumentChunk(document_fk=self.document_pk, index=chunk_index, chunk_text=chunk_text, embedding=embedding)
            session.add(chunk_db)
            session.commit()
        except Exception as e:
            raise Exception(f"_add_document_chunk_to_db : {e}")
