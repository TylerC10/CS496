package com.example.tyler.androidsqlite;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.content.DialogInterface;
import android.database.sqlite.SQLiteOpenHelper;
import android.database.sqlite.SQLiteDatabase;
import android.location.Location;
import android.provider.BaseColumns;
import android.support.v4.widget.SimpleCursorAdapter;
import android.support.v7.app.AlertDialog;
import android.content.Context;
import android.database.Cursor;
import android.view.View;
import android.content.pm.PackageManager;
import android.support.annotation.NonNull;
import android.support.annotation.Nullable;
import android.support.v4.app.ActivityCompat;
import android.widget.Button;
import android.widget.ListView;
import android.widget.EditText;
import android.content.ContentValues;
import android.util.Log;
import android.Manifest;
import android.app.Dialog;

import com.google.android.gms.location.LocationRequest;
import com.google.android.gms.common.GoogleApiAvailability;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.common.api.GoogleApiClient;
import com.google.android.gms.location.LocationListener;
import com.google.android.gms.common.ConnectionResult;


class SQLiteExample extends SQLiteOpenHelper {          //Taken right from lecture materials.

    public SQLiteExample(Context context) {
        super(context, DBContract.DemoTable.DB_NAME, null, DBContract.DemoTable.DB_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db){
        db.execSQL(DBContract.DemoTable.SQL_CREATE_DEMO_TABLE);

        ContentValues testValues = new ContentValues();
        testValues.put(DBContract.DemoTable.COLUMN_NAME_TEXT, "Text");
        testValues.put(DBContract.DemoTable.COLUMN_NAME_LAT, "Latitude");
        testValues.put(DBContract.DemoTable.COLUMN_NAME_LONG, "Longitude");
        db.insert(DBContract.DemoTable.TABLE_NAME, null, testValues);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion){
        db.execSQL(DBContract.DemoTable.SQL_DROP_DEMO_TABLE);
        onCreate(db);
    }
}

final class DBContract {        //Also taken from the lecture materials. Need columns for text, latitude, and longitude
    private DBContract(){};

    public final class DemoTable implements BaseColumns {
        public static final String DB_NAME = "lat_long";        //Name of the database
        public static final String TABLE_NAME = "Main";         //Name of the table
        public static final String COLUMN_NAME_TEXT = "Text";   //Name of each column
        public static final String COLUMN_NAME_LAT = "Latitude";
        public static final String COLUMN_NAME_LONG = "Longitude";
        public static final int DB_VERSION = 1;

        public static final String SQL_CREATE_DEMO_TABLE = "CREATE TABLE " +    //Create the table
                DemoTable.TABLE_NAME + "(" + DemoTable._ID + " INTEGER PRIMARY KEY NOT NULL," +
                DemoTable.COLUMN_NAME_TEXT + " VARCHAR(255)," +
                DemoTable.COLUMN_NAME_LAT + " VARCHAR(255)," +
                DemoTable.COLUMN_NAME_LONG + " VARCHAR(255));";

        public  static final String SQL_DROP_DEMO_TABLE = "DROP TABLE IF EXISTS " + DemoTable.TABLE_NAME;
    }
}

public class MainActivity extends AppCompatActivity implements GoogleApiClient.ConnectionCallbacks, GoogleApiClient.OnConnectionFailedListener{
    private String latitudeText;                    //Have to implement ConnectionCallbacks and OnConnectionFailedListener
    private String longitudeText;
    private GoogleApiClient mGoogleApiClient;       //Naming convetions for the variables was also from lecture material
    private LocationRequest mLocationRequest;
    private LocationListener mLocationListener;
    private Location mLastLocation;
    private static final String TAG = "SQLite";
    private static final int locationPermission = 15;
    SQLiteExample mSQLiteExample;
    Button mSQLSubmitButton;
    Cursor mSQLCursor;
    SimpleCursorAdapter mSQLCursorAdapter;
    SQLiteDatabase mSQLDB;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        latitudeText = "44.5";
        longitudeText = "-123.2";

        if(mGoogleApiClient == null){       //We need the Google API instance
            mGoogleApiClient = new GoogleApiClient.Builder(this)
                    .addConnectionCallbacks(this)
                    .addOnConnectionFailedListener(this)
                    .addApi(LocationServices.API)
                    .build();
        }
        mLocationRequest = LocationRequest.create();
        mLocationRequest.setPriority(LocationRequest.PRIORITY_HIGH_ACCURACY);
        mLocationRequest.setInterval(5000);             //High accuracy every five seconds
        mLocationRequest.setFastestInterval(5000);

        mLocationListener = new LocationListener() {    //Listen for location changes
            @Override
            public void onLocationChanged(Location location) {
                if(location != null){       //Set the latitude and longitude if location isn't null
                    latitudeText = String.valueOf(location.getLatitude());
                    longitudeText = String.valueOf(location.getLongitude());
                }
                else{       //Else throw an error
                    AlertDialog.Builder builder = new AlertDialog.Builder(MainActivity.this);
                    builder.setMessage("Did not get location.").setTitle("Failed.");
                    builder.setPositiveButton("OK", new DialogInterface.OnClickListener(){
                        public void onClick(DialogInterface dialog, int id){

                        }
                    });
                    AlertDialog dialog = builder.create();
                    dialog.show();
                }
            }
        };
        mSQLiteExample = new SQLiteExample(this);           //Get database instance
        mSQLDB = mSQLiteExample.getWritableDatabase();
        mSQLSubmitButton = (Button) findViewById(R.id.add); //Add functionality to the button

        mSQLSubmitButton.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View v){
                if(mSQLDB != null){
                    EditText text = (EditText) findViewById(R.id.edit); //Place all the text
                    String textContent = text.getText().toString();
                    text.setText("");
                    ContentValues values = new ContentValues();         //Make a new ContantValues to add data to the database
                    values.put(DBContract.DemoTable.COLUMN_NAME_TEXT, textContent);
                    values.put(DBContract.DemoTable.COLUMN_NAME_LAT, latitudeText);
                    values.put(DBContract.DemoTable.COLUMN_NAME_LONG, longitudeText);
                    mSQLDB.insert(DBContract.DemoTable.TABLE_NAME, null, values);   //Insert into database
                    showTable();
                }
                else{
                    Log.d(TAG, "Can't access database.");
                }
            }
        });
        showTable();
    }
    @Override                                   //The next several functions handle things like starting, connecting, and showing errors
    protected void onStart(){
        mGoogleApiClient.connect();
        super.onStart();;
    }

    @Override
    protected void onStop(){
        mGoogleApiClient.disconnect();
        super.onStop();
    }

    @Override
    public void onConnected(@Nullable Bundle bundle){   //Getting the correct location if permissions are correct
        if(ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_DENIED &&
                ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_DENIED){
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, locationPermission);
            return;
        }
        getLocation();
    }

    @Override
    public void onConnectionFailed(@NonNull ConnectionResult connectionReturn){
        Dialog showError = GoogleApiAvailability.getInstance().getErrorDialog(this, connectionReturn.getErrorCode(), 0);
        showError.show();
        return;
    }

    @Override
    public void onConnectionSuspended(int i){

    }

    @Override
    public void onRequestPermissionsResult(int requestNum, String[] permissionReturn, int[] resultReturn){
        if(requestNum == locationPermission){
            if(resultReturn.length > 0){
                getLocation();
            } else {
                latitudeText = "44.5";          //Set the defaults
                longitudeText = "-123.2";
            }
        }
    }


    private void showTable(){       //This function is used for querying and displaying information. It is taken from the lecture materials
        if(mSQLDB != null){
            try{
                if(mSQLCursorAdapter != null && mSQLCursorAdapter.getCursor() != null){
                    if(!mSQLCursorAdapter.getCursor().isClosed()){
                        mSQLCursorAdapter.getCursor().close();
                    }
                }

                mSQLCursor = mSQLDB.query(DBContract.DemoTable.TABLE_NAME, new String[]{DBContract.DemoTable._ID, DBContract.DemoTable.COLUMN_NAME_TEXT,
                                DBContract.DemoTable.COLUMN_NAME_LAT, DBContract.DemoTable.COLUMN_NAME_LONG},   //Create cursor for iterating
                        null, null, null, null, null);

                ListView viewSQLList = (ListView) findViewById(R.id.list);

                mSQLCursorAdapter = new SimpleCursorAdapter(this,
                        R.layout.sql_hold,
                        mSQLCursor,
                        new String[]{DBContract.DemoTable.COLUMN_NAME_TEXT, DBContract.DemoTable.COLUMN_NAME_LAT, DBContract.DemoTable.COLUMN_NAME_LONG},
                        new int[]{R.id.text, R.id.latitude, R.id.longitude},
                        0);
                viewSQLList.setAdapter(mSQLCursorAdapter);
            }
            catch (Exception e){
                Log.d(TAG, "Cannot load data.");
            }
        }
    }

    private void getLocation(){
        if(ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_DENIED) {
            return;
        }
        LocationServices.FusedLocationApi.requestLocationUpdates(mGoogleApiClient, mLocationRequest, mLocationListener);
        mLastLocation = LocationServices.FusedLocationApi.getLastLocation(mGoogleApiClient);
        if(mLastLocation != null) {
            latitudeText = String.valueOf(mLastLocation.getLatitude());
            longitudeText = String.valueOf(mLastLocation.getLongitude());
        } else {
            LocationServices.FusedLocationApi.requestLocationUpdates(mGoogleApiClient, mLocationRequest, mLocationListener);    //Use the most recent location
        }
    }
}



















