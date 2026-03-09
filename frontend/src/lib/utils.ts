import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number, symbol: string = "$"): string {
  const formatted = Math.abs(amount)
    .toFixed(2)
    .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return amount < 0 ? `${symbol} -${formatted}` : `${symbol} ${formatted}`;
}

export function formatDate(date: string): string {
  const d = new Date(date);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
}

export function formatDatetime(date: string): string {
  const d = new Date(date);
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${day}/${month}/${year} ${hours}:${minutes}`;
}

interface TributosResult {
  cif: number;
  adValorem: number;
  baseIgv: number;
  igv: number;
  ipm: number;
  percepcion: number;
  totalTributos: number;
}

export function calcularTributos(
  fob: number,
  flete: number,
  seguro: number,
  tasaAdValorem: number,
  tasaIgv: number = 18,
  tasaIpm: number = 0,
  tasaPercepcion: number = 3.5,
  montoIsc: number = 0
): TributosResult {
  const cif = fob + flete + seguro;
  const adValorem = cif * (tasaAdValorem / 100);
  const baseIgv = cif + adValorem + montoIsc;
  const igv = baseIgv * (tasaIgv / 100);
  const ipm = baseIgv * (tasaIpm / 100);
  const percepcion = (cif + adValorem + montoIsc + igv + ipm) * (tasaPercepcion / 100);
  const totalTributos = adValorem + igv + ipm + percepcion + montoIsc;

  return {
    cif,
    adValorem,
    baseIgv,
    igv,
    ipm,
    percepcion,
    totalTributos,
  };
}
