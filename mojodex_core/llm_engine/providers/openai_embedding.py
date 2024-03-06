from mojodex_core.llm_engine.embedding_provider import EmbeddingProvider

class OpenAIEmbeddingProvider(EmbeddingProvider):
    
    def get_embedding(self, text):
        """
        :param text: Text to embed
        :return: Embedding
        """
        embedding = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return embedding.data[0].embedding

    