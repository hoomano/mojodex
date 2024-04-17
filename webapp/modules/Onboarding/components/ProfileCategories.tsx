import Button from "components/Button";
import React, { useState } from "react";
import useGetProfileCategories from "../hooks/useGetProfileCategories";
import Card from "./Card";
import { ProfileCategory } from "../interface";

interface Props {
  onCategoryClick: (item: ProfileCategory) => void;
}


const ProfileCategories = ({ onCategoryClick }: Props) => {
  const { data } = useGetProfileCategories();

  return (
    <div className="grid sm:grid-cols-3 gap-[20px]">
      {data?.profile_categories?.map((item) => (
        <Card
          key={item.profile_category_pk}
          name={item.name}
          icon={item.emoji}
          definition={item.description}
          onClick={() => onCategoryClick(item)}
        />
      ))}
    </div>
  );

};

export default ProfileCategories;
