export interface UpdateCompanyDetailsPayload {
  correct: string | null;
  feedback: string;
}

export interface UserTask {
  user_task_pk: number;
  task_name: string;
  task_description: string;
  task_icon: string;
}

export interface BusinessGoal {
  goal: string;
}

export interface ProfileCategoryAPIResponse {
  profile_categories: ProfileCategory[];
}

export interface ProfileCategory {
  profile_category_pk: number;
  emoji: string;
  name: string;
  description: string;
}
