import React from 'react';
import { CheckCircle, Circle, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

interface WizardLayoutProps {
  currentStep: number;
  totalSteps: number;
  title: string;
  description: string;
  children: React.ReactNode;
  onNext?: () => void;
  onBack?: () => void;
  isNextDisabled?: boolean;
  isNextLoading?: boolean;
  nextLabel?: string;
}

export const WizardLayout: React.FC<WizardLayoutProps> = ({
  currentStep,
  totalSteps,
  title,
  description,
  children,
  onNext,
  onBack,
  isNextDisabled = false,
  isNextLoading = false,
  nextLabel = 'Next',
}) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Initial Setup
        </h2>

        {/* Step Indicators */}
        <div className="mt-4 flex justify-center space-x-4">
          {Array.from({ length: totalSteps }).map((_, index) => (
            <div key={index} className="flex items-center">
              {index < currentStep ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : index === currentStep ? (
                <Circle className="h-5 w-5 text-brand-600 fill-current" />
              ) : (
                <Circle className="h-5 w-5 text-gray-300" />
              )}
              {index < totalSteps - 1 && (
                <div className={clsx(
                  "h-0.5 w-8 ml-4",
                  index < currentStep ? "bg-green-500" : "bg-gray-300"
                )} />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="mb-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">{title}</h3>
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          </div>

          {children}

          <div className="mt-6 flex justify-between">
            {currentStep > 0 && (
              <button
                type="button"
                onClick={onBack}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500"
              >
                Back
              </button>
            )}
            <div className="flex-1" />
            <button
              type="button"
              onClick={onNext}
              disabled={isNextDisabled || isNextLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isNextLoading ? (
                <span className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
              ) : (
                nextLabel
              )}
              {!isNextLoading && nextLabel === 'Next' && <ChevronRight className="ml-2 h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
