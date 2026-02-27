package fasttime

import (
	"errors"
	"strconv"
	"strings"
	"time"
)

type Time time.Time

func (t *Time) UnmarshalJSON(data []byte) error {
	clean := strings.Trim(string(data), `"`)
	if clean == "" || clean == "null" {
		*t = Time{}
		return nil
	}
	ts, err := TS2int(clean)
	if err != nil {
		return err
	}
	*t = Time(Int2Time(ts))
	return nil
}

func (t Time) MarshalJSON() ([]byte, error) {
	ts := time.Time(t).UnixMicro()
	return []byte(`"` + Int2TS(ts) + `"`), nil
}

// SlackString returns the time as a slack timestamp (i.e. "1234567890.123456").
func (t Time) SlackString() string {
	return Int2TS(time.Time(t).UnixMicro())
}

var ErrNotATimestamp = errors.New("not a slack timestamp")

// Int2TS converts an int64 to a slack timestamp by inserting a dot in the
// right place.
func Int2TS(ts int64) string {
	const cut = 6
	s := strconv.FormatInt(ts, 10)
	l := len(s)
	if l < cut+1 {
		return ""
	}
	lo := s[l-cut:]
	hi := s[:l-cut]
	return hi + "." + lo
}

// Int2Time converts an int64 to a time.Time.
func Int2Time(ts int64) time.Time {
	return time.UnixMicro(ts)
}
