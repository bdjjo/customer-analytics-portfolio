"""Score one row per order with a locally trained return-risk prototype."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--model', type=Path, default=Path('models/return_risk.joblib'))
    args = parser.parse_args()
    bundle = joblib.load(args.model)
    data = pd.read_csv(args.input)
    missing = sorted(set(bundle['features']) - set(data.columns))
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    if data.empty:
        raise ValueError('Input file contains no orders')
    numeric = ['sales','units','line_count','category_count','discount_weighted','month']
    for col in numeric:
        data[col] = pd.to_numeric(data[col], errors='raise')
        if not np.isfinite(data[col]).all(): raise ValueError(f'Missing or non-finite values in {col}')
    if data[['segment','ship_mode']].isna().any().any():
        raise ValueError('Missing segment or ship_mode')
    if ((data['sales'] < 0) | (data['units'] <= 0) | (data['line_count'] <= 0) |
        (data['category_count'] <= 0) | ~data['month'].between(1,12) |
        ~data['discount_weighted'].between(0,1)).any():
        raise ValueError('One or more feature values are outside the permitted range')
    if not data[['units','line_count','category_count','month']].mod(1).eq(0).all().all():
        raise ValueError('Counts and month must be whole numbers')
    result = pd.DataFrame({'return_probability': bundle['model'].predict_proba(data[bundle['features']])[:, 1]})
    if 'order_reference' in data: result.insert(0, 'order_reference', data['order_reference'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f'Scored {len(result)} orders using {bundle["model_name"]}; results saved to {args.output}')

if __name__ == '__main__':
    main()
