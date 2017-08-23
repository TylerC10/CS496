package com.example.tyler.androidui;
import android.content.Intent;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        TextView verticalView = (TextView) findViewById(R.id.Layout2);
        verticalView.setOnClickListener(new View.OnClickListener(){

            @Override
            public void onClick(View v){
                Intent intent = new Intent(MainActivity.this, VerticalActivity.class);
                startActivity(intent);
            }
        });

        TextView horizontalView = (TextView) findViewById(R.id.Layout3);
        horizontalView.setOnClickListener(new View.OnClickListener(){

            @Override
            public void onClick(View v){
                Intent intent = new Intent(MainActivity.this, HorizontalActivity.class);
                startActivity(intent);
            }
        });

        TextView gridView = (TextView) findViewById(R.id.Layout4);
        gridView.setOnClickListener(new View.OnClickListener(){
            @Override
            public void onClick(View v){
                Intent intent = new Intent(MainActivity.this, GridActivity.class);
                startActivity(intent);
            }
        });

        TextView relativeView = (TextView) findViewById(R.id.Layout5);
        relativeView.setOnClickListener(new View.OnClickListener(){

            @Override
            public void onClick(View v){
                Intent intent = new Intent(MainActivity.this, RelativeActivity.class);
                startActivity(intent);
            }
        });

    }
}