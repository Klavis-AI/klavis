//go:build !386

package fasttime

import (
	"fmt"
	"strconv"
	"strings"
)

// TS2int converts a slack timestamp to an int64 by stripping the dot and
// converting the string to an int64.  It is useful for fast comparison.
func TS2int(ts string) (int64, error) {
	if ts == "" {
		return 0, nil
	}
	i := strings.IndexByte(ts, '.')
	if i == -1 {
		return 0, fmt.Errorf("%w: %q", ErrNotATimestamp, ts)
	}
	val, err := strconv.Atoi(ts[:i] + ts[i+1:])
	return int64(val), err
}
