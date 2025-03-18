'use client';

import { Driver } from '@/services/predictions';
import Image from 'next/image';
import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface DriverGridProps {
  drivers: Driver[];
  selectedDriver?: number;
  onSelect: (driverNumber: number) => void;
  title: string;
  description?: string;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export function DriverGrid({ 
  drivers, 
  selectedDriver, 
  onSelect, 
  title, 
  description,
  isExpanded = false,
  onToggleExpand
}: DriverGridProps) {
  const [hoveredDriver, setHoveredDriver] = useState<number | null>(null);

  const getDriverImagePath = (driver: Driver) => {
    // Split the name into first and last name
    const [firstName, ...lastNameParts] = driver.name.split(' ');
    const lastName = lastNameParts.join(' ');
    
    // Get the first 3 letters of first name and first 3 letters of last name
    const firstNameShort = firstName.slice(0, 3).toLowerCase();
    const lastNameShort = lastName.slice(0, 3).toLowerCase();
    
    // Use single digit for numbers 1-9, no padding
    const number = driver.number.toString();
    
    // Construct the filename in the format: {firstname}[3]{lastname}[3]{number}.avif
    return `/drivers/${firstNameShort}${lastNameShort}${number}.avif`;
  };

  const getFlagImagePath = (driver: Driver) => {
    return `/flags/${driver.flag_filename}`;
  };

  const selectedDriverInfo = drivers.find(d => d.number === selectedDriver);

  return (
    <div className="space-y-2">
      <button
        onClick={onToggleExpand}
        className="w-full flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
      >
        <div className="flex flex-col items-start">
          <h3 className="text-lg font-semibold">{title}</h3>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
          {selectedDriverInfo && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm font-medium">#{selectedDriverInfo.number}</span>
              <span className="text-sm">{selectedDriverInfo.name}</span>
              {selectedDriverInfo.nationality && (
                <Image
                  src={getFlagImagePath(selectedDriverInfo)}
                  alt={selectedDriverInfo.nationality}
                  width={20}
                  height={15}
                  className="rounded-sm"
                />
              )}
            </div>
          )}
        </div>
        {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
      </button>
      
      {isExpanded && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 p-4 border rounded-lg bg-card">
          {drivers.map((driver) => {
            const isSelected = selectedDriver === driver.number;
            const isHovered = hoveredDriver === driver.number;
            
            return (
              <button
                key={driver.number}
                onClick={() => onSelect(driver.number)}
                onMouseEnter={() => setHoveredDriver(driver.number)}
                onMouseLeave={() => setHoveredDriver(null)}
                className={`
                  relative group rounded-lg overflow-hidden border transition-all duration-200
                  ${isSelected 
                    ? 'border-primary bg-primary/10' 
                    : 'border-border hover:border-primary/50 hover:bg-accent/50'
                  }
                `}
              >
                <div className="aspect-square relative">
                  <Image
                    src={getDriverImagePath(driver)}
                    alt={driver.name}
                    fill
                    className="object-cover"
                    onError={(e: React.SyntheticEvent<HTMLImageElement, Event>) => {
                      const target = e.currentTarget;
                      target.src = '/drivers/fallback01.png';
                    }}
                  />
                  {driver.nationality && (
                    <div className="absolute top-2 right-2 z-10">
                      <Image
                        src={getFlagImagePath(driver)}
                        alt={driver.nationality}
                        width={24}
                        height={18}
                        className="rounded-sm shadow-md"
                      />
                    </div>
                  )}
                </div>
                
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <div className="absolute bottom-0 left-0 right-0 p-3 text-white">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">#{driver.number}</span>
                    </div>
                    <div className="text-sm font-medium truncate">{driver.name}</div>
                    <div className="text-xs text-white/80 truncate">{driver.team}</div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
} 