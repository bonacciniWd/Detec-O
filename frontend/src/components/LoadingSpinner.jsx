import React from 'react';

const LoadingSpinner = ({ size = 'md', className = '' }) => {
  let sizeClasses = 'w-8 h-8';
  
  if (size === 'sm') {
    sizeClasses = 'w-4 h-4';
  } else if (size === 'lg') {
    sizeClasses = 'w-12 h-12';
  }
  
  return (
    <div className={`flex justify-center items-center ${className}`}>
      <div className={`${sizeClasses} border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin`}></div>
    </div>
  );
};

export default LoadingSpinner; 