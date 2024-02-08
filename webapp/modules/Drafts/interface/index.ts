export interface Draft {
  produced_text_pk: number;
  user_task_execution_fk: number;
  user_id: string;
  production: string;
  title: string;
  creation_date: Date;
  idea_fk: string | null;
  text_type: string;
}

export interface SaveDraftPayload {
  datetime?: string;
  produced_text_pk?: number | null;
  production: string;
  title: string;
}

export interface GetAllDraftsPayload {
  nProducedText: number;
  offset: number;
}

export interface GetAllDraftsResponse {
  picture: string;
  name: string;
  produced_texts: Draft[];
}

export interface GetDraftResponse extends Draft {
  picture: string;
  name: string;
}

export interface EditerDraft {
  text: string;
  title: string;
  textPk: number | null;
}
