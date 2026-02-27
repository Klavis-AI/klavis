package fasttime

import (
	"math"
	"reflect"
	"strconv"
	"testing"
	"time"
)

func TestTs2int(t *testing.T) {
	type args struct {
		ts string
	}
	tests := []struct {
		name    string
		args    args
		want    int64
		wantErr bool
	}{
		{
			"valid ts",
			args{"1638494510.037400"},
			1638494510037400,
			false,
		},
		{
			"invalid ts",
			args{"x"},
			0,
			true,
		},
		{
			"real ts",
			args{"1674255434.388009"},
			1674255434388009,
			false,
		},
		{
			"maxint64",
			args{strconv.FormatInt(math.MaxInt64/1000, 10) + ".000"},
			math.MaxInt64 / 1000 * 1000,
			false,
		},
		{
			"no dot",
			args{"1674255434"},
			0,
			true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := TS2int(tt.args.ts)
			if (err != nil) != tt.wantErr {
				t.Errorf("TS2Int64() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if got != tt.want {
				t.Errorf("TS2Int64() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestInt2ts(t *testing.T) {
	type args struct {
		ts int64
	}
	tests := []struct {
		name string
		args args
		want string
	}{
		{
			"valid ts",
			args{1638494510037400},
			"1638494510.037400",
		},
		{
			"real ts",
			args{1674255434388009},
			"1674255434.388009",
		},
		{
			"zero",
			args{0},
			"",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Int2TS(tt.args.ts); got != tt.want {
				t.Errorf("Int642TS() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestInt2Time(t *testing.T) {
	type args struct {
		ts int64
	}
	tests := []struct {
		name string
		args args
		want time.Time
	}{
		{
			"valid ts",
			args{1645054781942979},
			time.Unix(1645054781, 942979000),
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := Int2Time(tt.args.ts); !reflect.DeepEqual(got, tt.want) {
				t.Errorf("Int2Time() = %v, want %v", got, tt.want)
			}
		})
	}
}

func BenchmarkTs2Int(b *testing.B) {
	var n int64
	for i := 0; i < b.N; i++ {
		n, _ = TS2int("1638494510.037400")
	}
	if n != 1638494510037400 {
		b.Errorf("Expected 1638494510037400, got %d", n)
	}
}

func BenchmarkInt2Ts(b *testing.B) {
	var s string

	for b.Loop() {
		s = Int2TS(1638494510037400)
	}
	if s != "1638494510.037400" {
		b.Errorf("Expected 1638494510.037400, got %s", s)
	}
}
