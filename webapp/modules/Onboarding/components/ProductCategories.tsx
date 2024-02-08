import Button from "components/Button";
import React, { useState } from "react";
import useGetProductCategories from "../hooks/useGetProductCategories";
import Card from "./Card";
import { ProductCategory } from "../interface";

interface Props {
  onCategoryClick: (item: ProductCategory) => void;
}


const ProductCategories = ({ onCategoryClick }: Props) => {
  const { data } = useGetProductCategories();

  return (
    <div className="grid sm:grid-cols-3 gap-[20px]">
      {data?.product_categories?.map((item) => (
        <Card
          key={item.product_category_pk}
          name={item.name}
          icon={item.emoji}
          definition={item.description}
          onClick={() => onCategoryClick(item)}
        />
      ))}
    </div>
  );

};

export default ProductCategories;
